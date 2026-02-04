"""Sensor platform for Smart Battery Charging."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_CHARGE, STATE_DISCHARGE, STATE_IDLE
from .coordinator import SmartBatteryCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Battery Charging sensors."""
    coordinator: SmartBatteryCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        CurrentPriceSensor(coordinator, entry),
        RecommendedStateSensor(coordinator, entry),
        PriceWindowsSensor(coordinator, entry, "cheapest"),
        PriceWindowsSensor(coordinator, entry, "expensive"),
        AveragePriceSensor(coordinator, entry),
        PriceSpreadSensor(coordinator, entry),
        PotentialSavingsSensor(coordinator, entry),
        NextCheapWindowSensor(coordinator, entry),
        NextExpensiveWindowSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class SmartBatterySensorBase(CoordinatorEntity[SmartBatteryCoordinator], SensorEntity):
    """Base class for Smart Battery Charging sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Smart Battery Charging",
            "manufacturer": "mavnezz",
            "model": "Smart Battery Charging",
            "sw_version": "0.3.0",
            "configuration_url": "https://github.com/mavnezz/smart_battery_charging",
        }

    @property
    def calculation(self) -> dict[str, Any] | None:
        """Return the calculation data."""
        if self.coordinator.data:
            return self.coordinator.data.get("calculation")
        return None


class CurrentPriceSensor(SmartBatterySensorBase):
    """Sensor for current electricity price."""

    _attr_name = "Current Price"
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/kWh"
    _attr_icon = "mdi:currency-eur"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_price"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.calculation:
            return self.calculation.get("current_price")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data:
            current = self.coordinator.data.get("current")
            if current:
                attrs["level"] = current.get("level")
                attrs["energy_price"] = current.get("energy")
                attrs["tax"] = current.get("tax")
        return attrs


class RecommendedStateSensor(SmartBatterySensorBase):
    """Sensor for recommended battery state."""

    _attr_name = "Recommended State"
    _attr_icon = "mdi:battery-charging"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_recommended_state"

    @property
    def native_value(self) -> str:
        """Return the recommended state."""
        if self.calculation:
            return self.calculation.get("recommended_state", STATE_IDLE)
        return STATE_IDLE

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        state = self.native_value
        if state == STATE_CHARGE:
            return "mdi:battery-charging"
        elif state == STATE_DISCHARGE:
            return "mdi:battery-arrow-down"
        return "mdi:battery"


class PriceWindowsSensor(SmartBatterySensorBase):
    """Sensor for price windows (cheapest or expensive)."""

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
        window_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._window_type = window_type
        self._attr_unique_id = f"{entry.entry_id}_{window_type}_windows"
        self._attr_name = f"{window_type.title()} Windows"
        self._attr_icon = (
            "mdi:currency-eur-off" if window_type == "cheapest" else "mdi:currency-eur"
        )

    @property
    def native_value(self) -> int:
        """Return count of windows."""
        if self.calculation:
            windows = self.calculation.get(f"{self._window_type}_windows", [])
            return len(windows)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the windows as attributes."""
        if self.calculation:
            return {
                "windows": self.calculation.get(f"{self._window_type}_windows", [])
            }
        return {"windows": []}


class AveragePriceSensor(SmartBatterySensorBase):
    """Sensor for average price."""

    _attr_name = "Average Price"
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/kWh"
    _attr_icon = "mdi:chart-line"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_average_price"

    @property
    def native_value(self) -> float | None:
        """Return the average price."""
        if self.calculation:
            return self.calculation.get("average_price")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return min/max prices."""
        if self.calculation:
            return {
                "min_price": self.calculation.get("min_price"),
                "max_price": self.calculation.get("max_price"),
            }
        return {}


class PriceSpreadSensor(SmartBatterySensorBase):
    """Sensor for price spread percentage."""

    _attr_name = "Price Spread"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:chart-bell-curve"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_price_spread"

    @property
    def native_value(self) -> float | None:
        """Return the price spread."""
        if self.calculation:
            return self.calculation.get("spread_percent")
        return None


class PotentialSavingsSensor(SmartBatterySensorBase):
    """Sensor for potential savings."""

    _attr_name = "Potential Savings"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/kWh"
    _attr_icon = "mdi:piggy-bank"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_potential_savings"

    @property
    def native_value(self) -> float | None:
        """Return potential savings per kWh."""
        if self.calculation:
            return self.calculation.get("potential_savings")
        return None


class NextCheapWindowSensor(SmartBatterySensorBase):
    """Sensor for next cheap window."""

    _attr_name = "Next Cheap Window"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-fast"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_cheap_window"

    @property
    def native_value(self):
        """Return next cheap window start time as datetime."""
        if self.coordinator.calculation_result:
            next_window = self.coordinator.calculation_engine.get_next_window(
                self.coordinator.calculation_result.cheapest_windows, "cheap"
            )
            if next_window and next_window.start:
                return next_window.start  # Return datetime object, not string
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return window details."""
        if self.coordinator.calculation_result:
            next_window = self.coordinator.calculation_engine.get_next_window(
                self.coordinator.calculation_result.cheapest_windows, "cheap"
            )
            if next_window:
                return {
                    "price": next_window.value,
                    "end": next_window.end.isoformat() if next_window.end else None,
                }
        return {}


class NextExpensiveWindowSensor(SmartBatterySensorBase):
    """Sensor for next expensive window."""

    _attr_name = "Next Expensive Window"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-alert"

    def __init__(
        self,
        coordinator: SmartBatteryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_expensive_window"

    @property
    def native_value(self):
        """Return next expensive window start time as datetime."""
        if self.coordinator.calculation_result:
            next_window = self.coordinator.calculation_engine.get_next_window(
                self.coordinator.calculation_result.expensive_windows, "expensive"
            )
            if next_window and next_window.start:
                return next_window.start  # Return datetime object, not string
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return window details."""
        if self.coordinator.calculation_result:
            next_window = self.coordinator.calculation_engine.get_next_window(
                self.coordinator.calculation_result.expensive_windows, "expensive"
            )
            if next_window:
                return {
                    "price": next_window.value,
                    "end": next_window.end.isoformat() if next_window.end else None,
                }
        return {}
