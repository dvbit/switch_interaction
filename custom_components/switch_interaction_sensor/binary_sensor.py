"""
Binary sensor platform for Switch Interaction Sensor.

IMPORTANT: Attributes are PERSISTENT/STATIC. They always reflect the
LAST interaction and are NEVER cleared. They update only on the next
toggle of the monitored entity.

State:
  on  — click window is open (at least one toggle registered)
  off — window expired (attributes still show last interaction data)

Extra state attributes (always visible, even when off):
  click_count      (int) — toggles counted in the last window
  interaction_type (str) — Physical | Automation | UI | Unknown
  user             (str) — HA user name or "Unknown"
  monitored_entity (str) — entity_id being tracked
  max_time_window  (int) — configured window in seconds

Interaction decoding from context:
  Physical  : parent_id=None,  user_id=None
  Automation: parent_id!=None, user_id=None
  UI        : parent_id=None,  user_id!=None
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
    CONF_NAME,
    DEFAULT_MAX_TIME,
    INTERACTION_AUTOMATION,
    INTERACTION_PHYSICAL,
    INTERACTION_UI,
    INTERACTION_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the binary sensor entity for this config entry."""
    entity_id: str = entry.data[CONF_ENTITY_ID]
    max_time: int = entry.data.get(CONF_MAX_TIME, DEFAULT_MAX_TIME)
    name: str = entry.data.get(CONF_NAME, entity_id)

    async_add_entities(
        [SwitchInteractionBinarySensor(hass, entry, entity_id, max_time, name)],
        update_before_add=False,
    )


class SwitchInteractionBinarySensor(BinarySensorEntity):
    """Binary sensor tracking switch/light interaction details.

    Attributes are STATIC: they persist across on/off cycles and
    only change when a new toggle event arrives.
    """

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        monitored_entity_id: str,
        max_time: int,
        name: str,
    ) -> None:
        """Initialise the sensor."""
        self._monitored_entity_id = monitored_entity_id
        self._max_time = max_time

        # --- PERSISTENT attributes (never cleared) ------------------------
        self._click_count: int = 0
        self._interaction_type: str = INTERACTION_UNKNOWN
        self._user_name: str = "Unknown"

        # --- Window tracking -----------------------------------------------
        self._window_active: bool = False
        self._cancel_reset: callback | None = None

        # --- Entity metadata -----------------------------------------------
        self._attr_unique_id = f"{entry.entry_id}_interaction"
        self._attr_name = name
        self._attr_icon = "mdi:gesture-tap"

    @property
    def is_on(self) -> bool:
        """Return True while the click window is open."""
        return self._window_active

    @property
    def extra_state_attributes(self) -> dict:
        """Return PERSISTENT attributes — always visible, even when off.

        These reflect the LAST interaction and are never cleared.
        """
        return {
            "click_count": self._click_count,
            "interaction_type": self._interaction_type,
            "user": self._user_name,
            "monitored_entity": self._monitored_entity_id,
            "max_time_window": self._max_time,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to state_changed events on the monitored entity."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._monitored_entity_id],
                self._async_state_changed,
            )
        )

    @callback
    def _async_state_changed(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle a toggle on the monitored entity."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        # Skip entity add/remove
        if new_state is None or old_state is None:
            return

        # Skip attribute-only updates — only count real on<->off toggles
        if new_state.state == old_state.state:
            return

        # --- Decode interaction type from context --------------------------
        context = new_state.context
        parent_id = context.parent_id
        user_id = context.user_id

        if parent_id is not None and user_id is None:
            interaction_type = INTERACTION_AUTOMATION
            user_name = "Unknown"
        elif parent_id is None and user_id is not None:
            interaction_type = INTERACTION_UI
            self.hass.async_create_task(self._async_resolve_user(user_id))
            user_name = user_id
        elif parent_id is None and user_id is None:
            interaction_type = INTERACTION_PHYSICAL
            user_name = "Unknown"
        else:
            interaction_type = INTERACTION_UI
            self.hass.async_create_task(self._async_resolve_user(user_id))
            user_name = user_id

        # --- Update PERSISTENT attributes ----------------------------------
        # New window: reset count to 1. Existing window: increment.
        if not self._window_active:
            self._click_count = 1
        else:
            self._click_count += 1

        self._interaction_type = interaction_type
        self._user_name = user_name
        self._window_active = True

        # --- (Re)start window timer ----------------------------------------
        if self._cancel_reset is not None:
            self._cancel_reset()

        self._cancel_reset = async_call_later(
            self.hass,
            timedelta(seconds=self._max_time),
            self._async_window_expired,
        )

        self.async_write_ha_state()

    async def _async_resolve_user(self, user_id: str) -> None:
        """Resolve user_id to display name via HA auth API."""
        try:
            user = await self.hass.auth.async_get_user(user_id)
            if user is not None:
                self._user_name = user.name or user_id
            else:
                self._user_name = user_id
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not resolve user_id %s", user_id)
            self._user_name = user_id
        self.async_write_ha_state()

    @callback
    def _async_window_expired(self, _now) -> None:
        """Window expired: sensor goes off but attributes are PRESERVED."""
        self._window_active = False
        self._cancel_reset = None
        # click_count, interaction_type, user are NOT touched
        self.async_write_ha_state()
