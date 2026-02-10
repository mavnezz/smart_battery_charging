"""Battery controller for Zendure Solarflow and other battery systems."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.const import ATTR_ENTITY_ID

from .const import (
    DOMAIN,
    STATE_CHARGE,
    STATE_DISCHARGE,
    STATE_IDLE,
    STATE_HOLD,
    STATE_OFF,
)

_LOGGER = logging.getLogger(__name__)


# Default entity patterns for Zendure Solarflow
ZENDURE_ENTITIES = {
    # Minimum SOC - this is the main control for charge/discharge
    "min_soc": "number.{device}_min_soc",
    # AC Mode selector (determines charge/discharge mode)
    "ac_mode": "select.{device}_ac_mode",
    # Maximum charge power input
    "max_charge": "number.{device}_maximum_charge",
    # Maximum discharge power output
    "max_discharge": "number.{device}_maximum_discharge",
    # Battery SOC (current level)
    "soc": "sensor.{device}_electric_level",
    # Output limit
    "output_limit": "number.{device}_output_limit",
    # Bypass mode
    "bypass_mode": "select.{device}_bypass_mode",
}

# SOC values for control via min_soc
SOC_CHARGE = 100  # Set min_soc to 100% to force charging
SOC_DISCHARGE = 10  # Set min_soc to 10% to allow full discharge
SOC_HOLD = 100  # Set min_soc to 100% to prevent discharge (hold charge)
SOC_IDLE = 50  # Set min_soc to 50% for idle/normal operation

# AC Mode values for Zendure (fallback)
AC_MODE_INPUT = "AC-Eingangsmodus"  # Charging from grid (German)
AC_MODE_OUTPUT = "AC-Ausgangsmodus"  # Discharging to home (German)
AC_MODE_DISABLED = "Deaktiviert"  # Neither charging nor discharging (German)


class BatteryController:
    """Controller for battery charge/discharge operations."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_name: str | None = None,
        custom_entities: dict[str, str] | None = None,
    ) -> None:
        """Initialize the battery controller.

        Args:
            hass: Home Assistant instance
            device_name: Zendure device name for entity ID resolution
            custom_entities: Custom entity mapping to override defaults
        """
        self.hass = hass
        self._device_name = device_name
        self._custom_entities = custom_entities or {}
        self._current_state = STATE_IDLE
        self._enabled = False

    def _get_entity_id(self, entity_type: str) -> str | None:
        """Get entity ID for a given type."""
        # Check custom entities first
        if entity_type in self._custom_entities:
            return self._custom_entities[entity_type]

        # Fall back to Zendure defaults
        if entity_type in ZENDURE_ENTITIES and self._device_name:
            return ZENDURE_ENTITIES[entity_type].format(device=self._device_name)

        return None

    async def async_set_state(
        self,
        state: str,
        charge_power: int | None = None,
        discharge_power: int | None = None,
    ) -> bool:
        """Set the battery state.

        Args:
            state: Target state (charge, discharge, idle, off)
            charge_power: Charging power in watts (optional)
            discharge_power: Discharging power in watts (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            _LOGGER.debug("Battery controller is disabled, skipping state change")
            return False

        try:
            if state == STATE_CHARGE:
                return await self._async_start_charging(charge_power)
            elif state == STATE_HOLD:
                return await self._async_set_hold()
            elif state == STATE_DISCHARGE:
                return await self._async_start_discharging(discharge_power)
            elif state == STATE_IDLE:
                return await self._async_set_idle()
            elif state == STATE_OFF:
                return await self._async_turn_off()
            else:
                _LOGGER.warning("Unknown battery state: %s", state)
                return False

        except Exception as err:
            _LOGGER.error("Error setting battery state to %s: %s", state, err)
            return False

    async def _async_start_charging(self, power: int | None = None) -> bool:
        """Start charging the battery by setting min_soc to 100%."""
        _LOGGER.info("Starting battery charging via min_soc=100%% (power: %s W)", power)

        # Set min_soc to 100% to force charging
        min_soc_entity = self._get_entity_id("min_soc")
        if min_soc_entity:
            await self._async_call_service(
                "number",
                "set_value",
                {ATTR_ENTITY_ID: min_soc_entity, "value": SOC_CHARGE},
            )
            _LOGGER.info("Set %s to %d%%", min_soc_entity, SOC_CHARGE)
        else:
            _LOGGER.warning("min_soc entity not found, trying AC mode fallback")
            # Fallback to AC mode
            ac_mode_entity = self._get_entity_id("ac_mode")
            if ac_mode_entity:
                await self._async_call_service(
                    "select",
                    "select_option",
                    {ATTR_ENTITY_ID: ac_mode_entity, "option": AC_MODE_INPUT},
                )

        self._current_state = STATE_CHARGE
        return True

    async def _async_set_hold(self) -> bool:
        """Hold battery at current level by keeping min_soc at 100%."""
        _LOGGER.info("Setting battery to HOLD via min_soc=%d%%", SOC_HOLD)

        min_soc_entity = self._get_entity_id("min_soc")
        if min_soc_entity:
            await self._async_call_service(
                "number",
                "set_value",
                {ATTR_ENTITY_ID: min_soc_entity, "value": SOC_HOLD},
            )
            _LOGGER.info("Set %s to %d%%", min_soc_entity, SOC_HOLD)
        else:
            _LOGGER.warning("min_soc entity not found for HOLD state")

        self._current_state = STATE_HOLD
        return True

    async def _async_start_discharging(self, power: int | None = None) -> bool:
        """Start discharging the battery by setting min_soc to minimum."""
        _LOGGER.info("Starting battery discharging via min_soc=%d%% (power: %s W)", SOC_DISCHARGE, power)

        # Set min_soc to low value to allow discharge
        min_soc_entity = self._get_entity_id("min_soc")
        if min_soc_entity:
            await self._async_call_service(
                "number",
                "set_value",
                {ATTR_ENTITY_ID: min_soc_entity, "value": SOC_DISCHARGE},
            )
            _LOGGER.info("Set %s to %d%%", min_soc_entity, SOC_DISCHARGE)
        else:
            _LOGGER.warning("min_soc entity not found, trying AC mode fallback")
            # Fallback to AC mode
            ac_mode_entity = self._get_entity_id("ac_mode")
            if ac_mode_entity:
                await self._async_call_service(
                    "select",
                    "select_option",
                    {ATTR_ENTITY_ID: ac_mode_entity, "option": AC_MODE_OUTPUT},
                )

        self._current_state = STATE_DISCHARGE
        return True

    async def _async_set_idle(self) -> bool:
        """Set battery to idle by setting min_soc to a middle value."""
        _LOGGER.info("Setting battery to idle via min_soc=%d%%", SOC_IDLE)

        # Set min_soc to a middle value
        min_soc_entity = self._get_entity_id("min_soc")
        if min_soc_entity:
            await self._async_call_service(
                "number",
                "set_value",
                {ATTR_ENTITY_ID: min_soc_entity, "value": SOC_IDLE},
            )
            _LOGGER.info("Set %s to %d%%", min_soc_entity, SOC_IDLE)
        else:
            _LOGGER.warning("min_soc entity not found, trying AC mode fallback")
            # Fallback to AC mode
            ac_mode_entity = self._get_entity_id("ac_mode")
            if ac_mode_entity:
                await self._async_call_service(
                    "select",
                    "select_option",
                    {ATTR_ENTITY_ID: ac_mode_entity, "option": AC_MODE_DISABLED},
                )

        self._current_state = STATE_IDLE
        return True

    async def _async_turn_off(self) -> bool:
        """Turn off the battery system."""
        _LOGGER.info("Turning off battery")
        # Same as idle for most battery systems
        return await self._async_set_idle()

    async def _async_call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any],
    ) -> None:
        """Call a Home Assistant service."""
        _LOGGER.debug(
            "Calling service %s.%s with data: %s",
            domain,
            service,
            service_data,
        )
        await self.hass.services.async_call(
            domain,
            service,
            service_data,
            blocking=True,
        )

    async def async_get_soc(self) -> float | None:
        """Get the current battery state of charge."""
        soc_entity = self._get_entity_id("soc")
        if not soc_entity:
            return None

        state = self.hass.states.get(soc_entity)
        if state and state.state not in ("unknown", "unavailable"):
            try:
                return float(state.state)
            except ValueError:
                return None
        return None

    @property
    def current_state(self) -> str:
        """Return the current battery state."""
        return self._current_state

    @property
    def enabled(self) -> bool:
        """Return whether the controller is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set whether the controller is enabled."""
        self._enabled = value
        if not value:
            _LOGGER.info("Battery controller disabled")
        else:
            _LOGGER.info("Battery controller enabled")

    def configure(
        self,
        device_name: str | None = None,
        custom_entities: dict[str, str] | None = None,
    ) -> None:
        """Update the controller configuration.

        Args:
            device_name: Zendure device name
            custom_entities: Custom entity mapping
        """
        if device_name is not None:
            self._device_name = device_name
        if custom_entities is not None:
            self._custom_entities = custom_entities


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for battery control."""

    async def handle_set_battery_state(call: ServiceCall) -> None:
        """Handle the set_battery_state service call."""
        state = call.data.get("state")
        charge_power = call.data.get("charge_power")
        discharge_power = call.data.get("discharge_power")

        # Get controller from first entry (or specified entry)
        entry_id = call.data.get("entry_id")
        if entry_id:
            data = hass.data[DOMAIN].get(entry_id)
        else:
            # Use first available entry
            for entry_data in hass.data[DOMAIN].values():
                if "battery_controller" in entry_data:
                    data = entry_data
                    break
            else:
                _LOGGER.error("No battery controller found")
                return

        controller = data.get("battery_controller")
        if controller:
            await controller.async_set_state(
                state,
                charge_power=charge_power,
                discharge_power=discharge_power,
            )

    hass.services.async_register(
        DOMAIN,
        "set_battery_state",
        handle_set_battery_state,
    )
