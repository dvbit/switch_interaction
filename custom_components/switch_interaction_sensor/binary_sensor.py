"""
Binary sensor platform for Switch Interaction Sensor.

Provides a single binary_sensor entity per config entry:
  on  = click window is active
  off = window expired (attributes on sibling sensors are preserved)

Linked to the device via DeviceInfo so it appears grouped with
the sensor entities (click_count, interaction_type, user).
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DOMAIN
from .coordinator import SwitchInteractionCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor from a config entry."""
    coordinator: SwitchInteractionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name: str = entry.data.get(CONF_NAME, "interaction")

    async_add_entities(
        [SwitchInteractionBinarySensor(coordinator, entry, name)],
        update_before_add=False,
    )


class SwitchInteractionBinarySensor(BinarySensorEntity):
    """Binary sensor: on while the click window is active."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:gesture-tap"

    def __init__(
        self,
        coordinator: SwitchInteractionCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialise the binary sensor."""
        self._coordinator = coordinator

        self._attr_unique_id = f"{entry.entry_id}_window"
        self._attr_name = "Window"

        # Link to device — all entities with same identifiers
        # appear under one device in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Switch Interaction Sensor",
            model="Virtual",
            entry_type=None,
        )

    @property
    def is_on(self) -> bool:
        """Return True while the click window is open."""
        return self._coordinator.window_active

    async def async_added_to_hass(self) -> None:
        """Register for coordinator updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        """React to coordinator state change."""
        self.async_write_ha_state()
