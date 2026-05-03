"""
Sensor platform for Switch Interaction Sensor.

Provides three sensor entities per config entry, all linked to the same
device as the binary_sensor:

  - Click Count      (int)  — number of toggles in the last window
  - Interaction Type  (str)  — Physical / Automation / UI / Unknown
  - User             (str)  — HA user name or "Unknown"

All values are PERSISTENT: they reflect the last interaction and are
only overwritten by the next toggle event.  They are never cleared.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up sensor entities from a config entry."""
    coordinator: SwitchInteractionCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name: str = entry.data.get(CONF_NAME, "interaction")

    # Shared DeviceInfo — same identifiers as binary_sensor
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Switch Interaction Sensor",
        model="Virtual",
        entry_type=None,
    )

    async_add_entities(
        [
            ClickCountSensor(coordinator, entry, device_info),
            InteractionTypeSensor(coordinator, entry, device_info),
            UserSensor(coordinator, entry, device_info),
        ],
        update_before_add=False,
    )


class _BaseSwitchInteractionSensor(SensorEntity):
    """Base class for all interaction sensor entities.

    Provides shared setup: coordinator subscription, device linkage,
    and the update callback pattern.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SwitchInteractionCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialise base sensor."""
        self._coordinator = coordinator
        self._attr_device_info = device_info

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


class ClickCountSensor(_BaseSwitchInteractionSensor):
    """Sensor: number of clicks in the last time window."""

    _attr_icon = "mdi:counter"

    def __init__(
        self,
        coordinator: SwitchInteractionCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialise click count sensor."""
        super().__init__(coordinator, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_click_count"
        self._attr_name = "Click Count"

    @property
    def native_value(self) -> int:
        """Return click count — PERSISTENT, never cleared."""
        return self._coordinator.click_count


class InteractionTypeSensor(_BaseSwitchInteractionSensor):
    """Sensor: type of the last interaction (Physical/Automation/UI)."""

    _attr_icon = "mdi:swap-horizontal"

    def __init__(
        self,
        coordinator: SwitchInteractionCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialise interaction type sensor."""
        super().__init__(coordinator, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_interaction_type"
        self._attr_name = "Interaction Type"

    @property
    def native_value(self) -> str:
        """Return interaction type — PERSISTENT, never cleared."""
        return self._coordinator.interaction_type


class UserSensor(_BaseSwitchInteractionSensor):
    """Sensor: HA user who triggered the last interaction."""

    _attr_icon = "mdi:account"

    def __init__(
        self,
        coordinator: SwitchInteractionCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        """Initialise user sensor."""
        super().__init__(coordinator, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_user"
        self._attr_name = "User"

    @property
    def native_value(self) -> str:
        """Return user name — PERSISTENT, never cleared."""
        return self._coordinator.user_name
