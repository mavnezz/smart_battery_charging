"""Switch platform for Smart Battery Charging."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartBatteryCoordinator
from .automation_handler import AutomationHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Battery Charging switches."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartBatteryCoordinator = data["coordinator"]
    automation_handler: AutomationHandler = data["automation_handler"]

    entities = [
        AutoModeSwitch(coordinator, automation_handler, entry),
    ]

    async_add_entities(entities)


class AutoModeSwitch(CoordinatorEntity[SmartBatteryCoordinator], SwitchEntity):
    """Switch to enable/disable automatic battery control."""

    _attr_has_entity_name = True
    _attr_name = "Auto Mode"
    _attr_icon = "mdi:robot"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        automation_handler: AutomationHandler,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._automation_handler = automation_handler
        self._attr_unique_id = f"{entry.entry_id}_auto_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Smart Battery Charging",
            "manufacturer": "mavnezz",
            "model": "Smart Battery Charging",
            "sw_version": "0.4.0",
            "configuration_url": "https://github.com/mavnezz/smart_battery_charging",
        }

    @property
    def is_on(self) -> bool:
        """Return true if auto mode is enabled."""
        return self._automation_handler.enabled

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        return "mdi:robot" if self.is_on else "mdi:robot-off"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.coordinator.calculation_result:
            return {
                "recommended_state": self.coordinator.calculation_result.recommended_state,
                "current_price": self.coordinator.calculation_result.current_price,
                "potential_savings": self.coordinator.calculation_result.potential_savings,
            }
        return {}

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on auto mode."""
        await self._automation_handler.async_enable()
        self.async_write_ha_state()
        _LOGGER.info("Smart Battery Charging auto mode enabled")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off auto mode."""
        await self._automation_handler.async_disable()
        self.async_write_ha_state()
        _LOGGER.info("Smart Battery Charging auto mode disabled")
