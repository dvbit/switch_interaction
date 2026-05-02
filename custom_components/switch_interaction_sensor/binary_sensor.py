"""
Binary sensor platform for Switch Interaction Sensor.

Creates a single binary_sensor entity per config entry that:

  • Listens to state_changed events on the monitored switch/light
  • Counts consecutive toggles within a configurable time window
  • Decodes the interaction source (Physical / Automation / UI)
    from the event's context object
  • Resolves the HA user name when the toggle comes from the UI

State:
  on  — at least one click registered (window still open)
  off — idle (window expired, counters reset)

Extra state attributes:
  click_count      (int)    — toggles since window opened
  interaction_type (str)    — Physical | Automation | UI | Unknown
  user             (str)    — HA user name or "Unknown"
  monitored_entity (str)    — entity_id being tracked
  max_time_window  (int)    — configured window in seconds

Interaction decoding — based on context fields of the new_state:
  ┌──────────────┬───────────┬──────────┐
  │ Interaction  │ parent_id │ user_id  │
  ├──────────────┼───────────┼──────────┤
  │ Physical     │ None      │ None     │
  │ Automation   │ set       │ None     │
  │ UI           │ None      │ set      │
  └──────────────┴───────────┴──────────┘
  Ref: https://data.home-assistant.io/docs/context/
  Ref: https://community.home-assistant.io/t/400352/8

Key HA APIs used:
  async_track_state_change_event — per-entity listener (replaces deprecated
      async_track_state_change since HA 2024.5)
      Ref: https://developers.home-assistant.io/blog/2024/04/13/deprecate_async_track_state_change/
  async_call_later — one-shot timer for window reset
  hass.auth.async_get_user — resolve user_id → display name
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)

from .const import (
    CONF_ENTITY_ID,
    CONF_MAX_TIME,
    DEFAULT_MAX_TIME,
    INTERACTION_AUTOMATION,
    INTERACTION_PHYSICAL,
    INTERACTION_UI,
    INTERACTION_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Platform setup — called by __init__.async_setup_entry via
# hass.config_entries.async_forward_entry_setups()
# ---------------------------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the binary sensor entity for this config entry."""
    entity_id: str = entry.data[CONF_ENTITY_ID]
    max_time: int = entry.data.get(CONF_MAX_TIME, DEFAULT_MAX_TIME)

    async_add_entities(
        [SwitchInteractionBinarySensor(hass, entry, entity_id, max_time)],
        # No initial update needed — sensor starts idle (off)
        update_before_add=False,
    )


class SwitchInteractionBinarySensor(BinarySensorEntity):
    """Binary sensor that tracks switch/light interaction details.

    Lifecycle:
      __init__           → store config, set initial state
      async_added_to_hass → subscribe to state_changed events
      (async_on_remove)  → auto-unsubscribe on unload
    """

    # -- Entity registration hints ------------------------------------------
    _attr_has_entity_name = True   # name is relative to device/entry
    _attr_should_poll = False      # event-driven, no polling needed

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        monitored_entity_id: str,
        max_time: int,
    ) -> None:
        """Initialise internal state.

        Args:
            hass: Home Assistant instance.
            entry: The ConfigEntry that created this sensor.
            monitored_entity_id: The switch.* / light.* entity to watch.
            max_time: Click-counting window in seconds.
        """
        # --- Monitored entity config ---------------------------------------
        self._monitored_entity_id = monitored_entity_id
        self._max_time = max_time

        # --- Click / interaction tracking ----------------------------------
        self._click_count: int = 0
        self._interaction_type: str = INTERACTION_UNKNOWN
        self._user_name: str = "Unknown"

        # Handle returned by async_call_later(); call it to cancel the timer
        self._cancel_reset: callback | None = None

        # --- Entity metadata -----------------------------------------------
        self._attr_unique_id = f"{entry.entry_id}_interaction"
        self._attr_name = "Interaction"
        self._attr_icon = "mdi:gesture-tap"

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def is_on(self) -> bool:
        """Binary state: on while the click window is open."""
        return self._click_count > 0

    @property
    def extra_state_attributes(self) -> dict:
        """Expose click count, interaction type and user as attributes.

        These can be read in automations via e.g.:
          {{ state_attr('binary_sensor.xxx_interaction', 'click_count') }}
        """
        return {
            "click_count": self._click_count,
            "interaction_type": self._interaction_type,
            "user": self._user_name,
            "monitored_entity": self._monitored_entity_id,
            "max_time_window": self._max_time,
        }

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """Subscribe to state_changed events on the monitored entity.

        Uses async_track_state_change_event (per-entity indexed listener)
        instead of the deprecated async_track_state_change.
        The returned unsubscribe callable is registered via
        async_on_remove() so it is automatically cancelled on unload.
        """
        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._monitored_entity_id],
                self._async_state_changed,
            )
        )

    # -----------------------------------------------------------------------
    # Event handler
    # -----------------------------------------------------------------------
    @callback
    def _async_state_changed(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Process a state_changed event on the monitored entity.

        Steps:
          1. Ignore attribute-only updates (state unchanged).
          2. Decode interaction type from context.parent_id / user_id.
          3. Increment click counter.
          4. (Re)start the reset timer.
        """
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        # Guard: entity added/removed → one side is None
        if new_state is None or old_state is None:
            return

        # Guard: only count real toggles (on↔off), skip attribute updates
        if new_state.state == old_state.state:
            return

        # --- Decode interaction type from context --------------------------
        # Ref: https://data.home-assistant.io/docs/context/
        #   Physical  : parent_id=None  AND user_id=None
        #   Automation: parent_id!=None AND user_id=None
        #   UI        : parent_id=None  AND user_id!=None
        context = new_state.context
        parent_id = context.parent_id
        user_id = context.user_id

        if parent_id is not None and user_id is None:
            # Automation triggered the change
            interaction_type = INTERACTION_AUTOMATION
            user_name = "Unknown"

        elif parent_id is None and user_id is not None:
            # User toggled via dashboard / companion app
            interaction_type = INTERACTION_UI
            # Kick off async user-name resolution (updates attribute later)
            self.hass.async_create_task(
                self._async_resolve_user(user_id)
            )
            user_name = user_id  # placeholder until resolved

        elif parent_id is None and user_id is None:
            # Physical switch toggle
            interaction_type = INTERACTION_PHYSICAL
            user_name = "Unknown"

        else:
            # Edge case: both parent_id AND user_id set.
            # Treat as UI interaction (user triggered via automation UI).
            interaction_type = INTERACTION_UI
            self.hass.async_create_task(
                self._async_resolve_user(user_id)
            )
            user_name = user_id

        # --- Update state --------------------------------------------------
        self._interaction_type = interaction_type
        self._user_name = user_name
        self._click_count += 1

        # --- (Re)start the reset timer -------------------------------------
        # Cancel previous timer if the user clicks again within the window
        if self._cancel_reset is not None:
            self._cancel_reset()

        # Schedule _async_reset after max_time seconds
        self._cancel_reset = async_call_later(
            self.hass,
            timedelta(seconds=self._max_time),
            self._async_reset,
        )

        # Push new state to HA state machine
        self.async_write_ha_state()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    async def _async_resolve_user(self, user_id: str) -> None:
        """Translate a user_id into a human-readable display name.

        Uses hass.auth.async_get_user() — the standard HA auth API.
        Falls back to the raw user_id on any error.
        """
        try:
            user = await self.hass.auth.async_get_user(user_id)
            if user is not None:
                self._user_name = user.name or user_id
            else:
                self._user_name = user_id
        except Exception:  # noqa: BLE001 — broad catch is intentional
            _LOGGER.debug("Could not resolve user_id %s", user_id)
            self._user_name = user_id

        # Refresh state so the resolved name appears in attributes
        self.async_write_ha_state()

    @callback
    def _async_reset(self, _now) -> None:
        """Reset all counters after the click window expires.

        Called by async_call_later() when max_time seconds have elapsed
        since the last toggle.  Sensor transitions from on → off.
        """
        self._click_count = 0
        self._interaction_type = INTERACTION_UNKNOWN
        self._user_name = "Unknown"
        self._cancel_reset = None
        self.async_write_ha_state()
