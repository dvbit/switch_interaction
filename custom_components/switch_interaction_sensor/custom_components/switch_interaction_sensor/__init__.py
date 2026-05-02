"""
The Switch Interaction Sensor integration.

This integration creates a binary_sensor that monitors a switch or light
entity and exposes click count, interaction type (Physical / Automation /
UI) and the acting user as state attributes.

Lifecycle:
  async_setup_entry  — forwards setup to the binary_sensor platform
  async_unload_entry — tears down platform listeners cleanly

Ref: https://developers.home-assistant.io/docs/config_entries_index
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

# Platforms that this integration provides (only binary_sensor)
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Switch Interaction Sensor from a config entry.

    Called by HA core when the user adds the integration via the UI.
    Delegates entity creation to binary_sensor.async_setup_entry().

    Ref: https://developers.home-assistant.io/docs/config_entries_index
    """
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Called when the user removes the integration.  Ensures all event
    listeners registered via async_on_remove() are properly cancelled.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
