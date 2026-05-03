"""
Coordinator for Switch Interaction Sensor.

Holds the shared interaction state (click_count, interaction_type, user,
window_active) for a single monitored entity.  All platform entities
(binary_sensor + sensors) read from this coordinator.

Listens to state_changed events on the monitored entity and decodes the
interaction source from the context object:
  Physical  : parent_id=None,  user_id=None
  Automation: parent_id!=None, user_id=None
  UI        : parent_id=None,  user_id!=None
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)

from .const import (
    INTERACTION_AUTOMATION,
    INTERACTION_PHYSICAL,
    INTERACTION_UI,
    INTERACTION_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class SwitchInteractionCoordinator:
    """Shared state holder for one monitored entity.

    Attributes are PERSISTENT: they always reflect the last interaction
    and are only overwritten by a new toggle event.  When the click
    window expires, only window_active changes to False.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        monitored_entity_id: str,
        max_time: int,
    ) -> None:
        """Initialise coordinator."""
        self.hass = hass
        self.monitored_entity_id = monitored_entity_id
        self.max_time = max_time

        # --- PERSISTENT state (never cleared) ------------------------------
        self.click_count: int = 0
        self.interaction_type: str = INTERACTION_UNKNOWN
        self.user_name: str = "Unknown"

        # --- Window state --------------------------------------------------
        self.window_active: bool = False
        self._cancel_reset: callback | None = None

        # Callbacks registered by entities to be notified of updates
        self._listeners: list[callback] = []

    def async_add_listener(self, listener: callback) -> callback:
        """Register a listener. Returns a callable to remove it."""
        self._listeners.append(listener)

        def remove():
            self._listeners.remove(listener)

        return remove

    def _async_notify_listeners(self) -> None:
        """Notify all registered entities to update their state."""
        for listener in self._listeners:
            listener()

    async def async_start(self) -> callback:
        """Start listening to state changes. Returns unsubscribe callable."""
        return async_track_state_change_event(
            self.hass,
            [self.monitored_entity_id],
            self._async_state_changed,
        )

    @callback
    def _async_state_changed(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle a toggle on the monitored entity."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or old_state is None:
            return

        # Only count real on<->off toggles, skip attribute-only updates
        if new_state.state == old_state.state:
            return

        # --- Decode interaction type from context --------------------------
        context = new_state.context
        parent_id = context.parent_id
        user_id = context.user_id

        if parent_id is not None and user_id is None:
            self.interaction_type = INTERACTION_AUTOMATION
            self.user_name = "Unknown"
        elif parent_id is None and user_id is not None:
            self.interaction_type = INTERACTION_UI
            self.user_name = user_id  # placeholder until resolved
            self.hass.async_create_task(self._async_resolve_user(user_id))
        elif parent_id is None and user_id is None:
            self.interaction_type = INTERACTION_PHYSICAL
            self.user_name = "Unknown"
        else:
            # Edge case: both set — treat as UI
            self.interaction_type = INTERACTION_UI
            self.user_name = user_id
            self.hass.async_create_task(self._async_resolve_user(user_id))

        # --- Update click count --------------------------------------------
        if not self.window_active:
            self.click_count = 1
        else:
            self.click_count += 1

        self.window_active = True

        # --- (Re)start window timer ----------------------------------------
        if self._cancel_reset is not None:
            self._cancel_reset()

        self._cancel_reset = async_call_later(
            self.hass,
            timedelta(seconds=self.max_time),
            self._async_window_expired,
        )

        self._async_notify_listeners()

    async def _async_resolve_user(self, user_id: str) -> None:
        """Resolve user_id to display name via HA auth API."""
        try:
            user = await self.hass.auth.async_get_user(user_id)
            if user is not None:
                self.user_name = user.name or user_id
            else:
                self.user_name = user_id
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not resolve user_id %s", user_id)
            self.user_name = user_id
        self._async_notify_listeners()

    @callback
    def _async_window_expired(self, _now) -> None:
        """Window expired: sensor goes off, attributes are PRESERVED."""
        self.window_active = False
        self._cancel_reset = None
        self._async_notify_listeners()
