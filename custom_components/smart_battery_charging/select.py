"""Select platform for Smart Battery Charging."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_CHARGE, STATE_DISCHARGE, STATE_IDLE
from .coordinator import SmartBatteryCoordinator
from .automation_handler import AutomationHandler

_LOGGER = logging.getLogger(__name__)

# Operating modes
MODE_OFF = "off"
MODE_AUTO = "auto"
MODE_CHARGE = "charge"
MODE_DISCHARGE = "discharge"

MODE_LABELS = {
    MODE_OFF: "Deaktiviert",
    MODE_AUTO: "Automatik",
    MODE_CHARGE: "Laden",
    MODE_DISCHARGE: "Entladen",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Battery Charging select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SmartBatteryCoordinator = data["coordinator"]
    automation_handler: AutomationHandler = data["automation_handler"]

    entities = [
        OperatingModeSelect(coordinator, automation_handler, entry),
    ]

    async_add_entities(entities)


class OperatingModeSelect(CoordinatorEntity[SmartBatteryCoordinator], SelectEntity):
    """Select entity for battery operating mode."""

    _attr_has_entity_name = True
    _attr_name = "Betriebsmodus"
    _attr_icon = "mdi:battery-sync"
    _attr_options = [MODE_OFF, MODE_AUTO, MODE_CHARGE, MODE_DISCHARGE]

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        automation_handler: AutomationHandler,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._automation_handler = automation_handler
        self._attr_unique_id = f"{entry.entry_id}_operating_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Smart Battery Charging",
            "manufacturer": "mavnezz",
            "model": "Tibber Price Optimizer",
            "sw_version": "0.2.9",
        }

    @property
    def current_option(self) -> str:
        """Return the current operating mode."""
        return self._automation_handler.mode

    @property
    def icon(self) -> str:
        """Return icon based on current mode."""
        mode = self.current_option
        if mode == MODE_OFF:
            return "mdi:battery-off"
        elif mode == MODE_AUTO:
            return "mdi:battery-sync"
        elif mode == MODE_CHARGE:
            return "mdi:battery-charging"
        elif mode == MODE_DISCHARGE:
            return "mdi:battery-arrow-down"
        return "mdi:battery"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        attrs = {
            "mode_label": MODE_LABELS.get(self.current_option, self.current_option),
        }
        if self.coordinator.calculation_result:
            attrs["recommended_state"] = self.coordinator.calculation_result.recommended_state
            attrs["current_price"] = self.coordinator.calculation_result.current_price
            attrs["potential_savings"] = self.coordinator.calculation_result.potential_savings
        return attrs

    async def async_select_option(self, option: str) -> None:
        """Change the operating mode."""
        await self._automation_handler.async_set_mode(option)
        self.async_write_ha_state()
        _LOGGER.info("Smart Battery Charging mode set to: %s", option)
