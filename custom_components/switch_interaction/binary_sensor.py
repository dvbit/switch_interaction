"""Binary sensor platform for Switch Interaction Tracker."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CLICKS,
    ATTR_INTERACTION,
    ATTR_LAST_CHANGED,
    ATTR_USER,
    CONF_ENTITIES,
    CONF_MAXTIME,
    DEFAULT_MAXTIME,
    DOMAIN,
    INTERACTION_AUTOMATION,
    INTERACTION_PHYSICAL,
    INTERACTION_UI,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    entities = config_entry.data.get(CONF_ENTITIES, [])
    maxtime = config_entry.data.get(CONF_MAXTIME, DEFAULT_MAXTIME)

    sensors = [
        SwitchInteractionSensor(hass, entity_id, maxtime) for entity_id in entities
    ]

    async_add_entities(sensors, True)


class SwitchInteractionSensor(BinarySensorEntity):
    """Representation of a Switch Interaction binary sensor."""

    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entity_id: str, maxtime: int) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._monitored_entity = entity_id
        self._maxtime = maxtime

        # Generate unique_id and entity_id for this sensor
        entity_name = entity_id.replace(".", "_")
        self._attr_unique_id = f"interaction_{entity_name}"
        self.entity_id = f"binary_sensor.interaction_{entity_name}"
        self._attr_name = f"Interaction {entity_id}"

        # State attributes
        self._attr_is_on = False
        self._interaction_type: str | None = None
        self._user: str | None = "unknown"
        self._clicks = 0
        self._last_changed: datetime | None = None

        # Click counting
        self._click_count = 0
        self._click_timer = None
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Start listening to state changes
        self._remove_listener = async_track_state_change_event(
            self.hass,
            [self._monitored_entity],
            self._async_state_changed_listener,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._remove_listener:
            self._remove_listener()

        if self._click_timer:
            self._click_timer.cancel()

    async def _async_get_user_name(self, user_id: str) -> None:
        """Get user name from user_id."""
        try:
            user = await self.hass.auth.async_get_user(user_id)
            if user:
                self._user = user.name or user_id
            else:
                self._user = user_id
        except Exception as err:
            _LOGGER.warning("Could not get user name for %s: %s", user_id, err)
            self._user = user_id

        # Update state after getting user name
        self.async_write_ha_state()

    @callback
    def _async_state_changed_listener(self, event: Event) -> None:
        """Handle state changes of monitored entity."""
        new_state: State | None = event.data.get("new_state")

        if new_state is None:
            return

        # Get context information
        context = new_state.context

        # Determine interaction type based on context
        # Physical: id not null, parent_id null, user_id null
        # Automation: id not null, parent_id not null, user_id null
        # UI: id not null, parent_id null, user_id not null

        if context.id is not None:
            if context.parent_id is None and context.user_id is None:
                self._interaction_type = INTERACTION_PHYSICAL
                self._user = "unknown"
            elif context.parent_id is not None and context.user_id is None:
                self._interaction_type = INTERACTION_AUTOMATION
                self._user = "unknown"
            elif context.parent_id is None and context.user_id is not None:
                self._interaction_type = INTERACTION_UI
                # Get user name from user_id asynchronously
                asyncio.create_task(self._async_get_user_name(context.user_id))
            else:
                self._interaction_type = "unknown"
                self._user = "unknown"

        self._last_changed = dt_util.now()

        # Handle click counting
        self._handle_click()

        # Update the sensor state temporarily (will be reset after maxtime)
        self.async_write_ha_state()

    def _handle_click(self) -> None:
        """Handle click counting logic."""
        if self._click_count == 0:
            # First click, start timer
            self._click_count = 1
            _LOGGER.debug(
                "First click detected for %s, starting timer for %d seconds",
                self._monitored_entity,
                self._maxtime,
            )

            # Cancel existing timer if any
            if self._click_timer:
                self._click_timer.cancel()

            # Schedule click count finalization
            self._click_timer = self.hass.loop.call_later(
                self._maxtime, lambda: asyncio.create_task(self._async_finalize_clicks())
            )
        else:
            # Subsequent click within the time window
            self._click_count += 1
            _LOGGER.debug(
                "Click %d detected for %s",
                self._click_count,
                self._monitored_entity,
            )

    async def _async_finalize_clicks(self) -> None:
        """Finalize click count and turn on the sensor."""
        self._clicks = self._click_count
        self._attr_is_on = True

        _LOGGER.debug(
            "Finalizing %d clicks for %s - turning sensor ON",
            self._clicks,
            self._monitored_entity,
        )

        self.async_write_ha_state()

        # Turn off sensor immediately after turning on
        await asyncio.sleep(0.1)
        self._attr_is_on = False
        self._click_count = 0
        self._click_timer = None

        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            ATTR_INTERACTION: self._interaction_type,
            ATTR_USER: self._user,
            ATTR_CLICKS: self._clicks,
            ATTR_LAST_CHANGED: self._last_changed.isoformat() if self._last_changed else None,
            "monitored_entity": self._monitored_entity,
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:gesture-tap" if self._attr_is_on else "mdi:gesture-tap-hold"
