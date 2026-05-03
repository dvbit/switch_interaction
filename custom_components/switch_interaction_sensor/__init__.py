"""
The Switch Interaction Sensor integration.

Creates a device with a binary_sensor and three sensor entities that
monitor a switch/light and expose click count, interaction type and user.

Architecture:
  ConfigEntry -> Coordinator (shared state) -> binary_sensor + sensor entities
  All entities share the same DeviceInfo so they appear under one device.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_ENTITY_ID, CONF_MAX_TIME, DEFAULT_MAX_TIME, DOMAIN
from .coordinator import SwitchInteractionCoordinator

# Both platforms read from the shared coordinator
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry.

    1. Create the coordinator (shared state + event listener).
    2. Store it in hass.data so both platforms can access it.
    3. Forward setup to binary_sensor and sensor platforms.
    """
    entity_id: str = entry.data[CONF_ENTITY_ID]
    max_time: int = entry.data.get(CONF_MAX_TIME, DEFAULT_MAX_TIME)

    # Create coordinator and start listening
    coordinator = SwitchInteractionCoordinator(hass, entity_id, max_time)
    unsub = await coordinator.async_start()

    # Store coordinator and unsubscribe handle
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "unsub": unsub,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from state_changed events
    data = hass.data[DOMAIN].pop(entry.entry_id)
    data["unsub"]()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
