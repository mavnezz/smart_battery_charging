"""Automation handler for automatic battery control based on price recommendations."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval, async_call_later
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    STATE_CHARGE,
    STATE_DISCHARGE,
    STATE_IDLE,
    CONF_BATTERY_CAPACITY,
    DEFAULT_BATTERY_EFFICIENCY,
)

if TYPE_CHECKING:
    from .coordinator import SmartBatteryCoordinator
    from .battery_controller import BatteryController

_LOGGER = logging.getLogger(__name__)

# Check interval in seconds
AUTO_CHECK_INTERVAL = 60

# Operating modes
MODE_OFF = "off"
MODE_AUTO = "auto"
MODE_CHARGE = "charge"
MODE_DISCHARGE = "discharge"


class AutomationHandler:
    """Handler for automatic battery control based on price windows."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "SmartBatteryCoordinator",
        battery_controller: "BatteryController",
        entry_id: str,
    ) -> None:
        """Initialize the automation handler."""
        self.hass = hass
        self.coordinator = coordinator
        self.battery_controller = battery_controller
        self.entry_id = entry_id
        self._mode = MODE_OFF
        self._cancel_timer = None
        self._last_state = STATE_IDLE
        self._min_soc = 10  # Minimum SOC before stopping discharge
        self._max_soc = 100  # Maximum SOC before stopping charge

    @property
    def mode(self) -> str:
        """Return the current operating mode."""
        return self._mode

    @property
    def enabled(self) -> bool:
        """Return whether automatic control is enabled (for backwards compatibility)."""
        return self._mode != MODE_OFF

    async def async_set_mode(self, mode: str) -> None:
        """Set the operating mode."""
        if mode == self._mode:
            return

        old_mode = self._mode
        self._mode = mode

        # Cancel any existing timer
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None

        if mode == MODE_OFF:
            # Set battery to idle first, then disable controller
            self.battery_controller.enabled = True  # Temporarily enable to set state
            await self.battery_controller.async_set_state(STATE_IDLE)
            self.battery_controller.enabled = False
            self._last_state = STATE_IDLE
            _LOGGER.info("Battery control disabled, set to idle")

        elif mode == MODE_AUTO:
            # Enable automatic mode with periodic checks
            self.battery_controller.enabled = True
            self._cancel_timer = async_track_time_interval(
                self.hass,
                self._async_check_and_update,
                timedelta(seconds=AUTO_CHECK_INTERVAL),
            )
            # Run initial check
            await self._async_check_and_update(dt_util.now())
            _LOGGER.info("Automatic battery control enabled")

        elif mode == MODE_CHARGE:
            # Force charging mode
            self.battery_controller.enabled = True
            charge_power = self._get_charge_power()
            await self.battery_controller.async_set_state(
                STATE_CHARGE, charge_power=charge_power
            )
            self._last_state = STATE_CHARGE
            _LOGGER.info("Forced charging mode enabled")

        elif mode == MODE_DISCHARGE:
            # Force discharging mode
            self.battery_controller.enabled = True
            discharge_power = self._get_discharge_power()
            await self.battery_controller.async_set_state(
                STATE_DISCHARGE, discharge_power=discharge_power
            )
            self._last_state = STATE_DISCHARGE
            _LOGGER.info("Forced discharging mode enabled")

    async def async_enable(self) -> None:
        """Enable automatic battery control (backwards compatibility)."""
        await self.async_set_mode(MODE_AUTO)

    async def async_disable(self) -> None:
        """Disable automatic battery control (backwards compatibility)."""
        await self.async_set_mode(MODE_OFF)

    async def _async_check_and_update(self, now: datetime) -> None:
        """Check price windows and update battery state if needed."""
        if self._mode != MODE_AUTO:
            return

        try:
            # Get current recommendation from coordinator
            result = self.coordinator.calculation_result
            if not result:
                _LOGGER.debug("No calculation result available")
                return

            recommended_state = result.recommended_state

            # Check SOC limits before acting
            current_soc = await self.battery_controller.async_get_soc()

            if current_soc is not None:
                # Don't discharge if SOC is too low
                if recommended_state == STATE_DISCHARGE and current_soc <= self._min_soc:
                    _LOGGER.info(
                        "SOC (%.1f%%) at minimum, skipping discharge", current_soc
                    )
                    recommended_state = STATE_IDLE

                # Don't charge if SOC is at maximum
                if recommended_state == STATE_CHARGE and current_soc >= self._max_soc:
                    _LOGGER.info(
                        "SOC (%.1f%%) at maximum, skipping charge", current_soc
                    )
                    recommended_state = STATE_IDLE

            # Only act if state changed
            if recommended_state != self._last_state:
                _LOGGER.info(
                    "Battery state changing from %s to %s",
                    self._last_state,
                    recommended_state,
                )

                # Determine power settings based on state
                charge_power = None
                discharge_power = None

                if recommended_state == STATE_CHARGE:
                    charge_power = self._get_charge_power()
                elif recommended_state == STATE_DISCHARGE:
                    discharge_power = self._get_discharge_power()

                # Set the new state
                success = await self.battery_controller.async_set_state(
                    recommended_state,
                    charge_power=charge_power,
                    discharge_power=discharge_power,
                )

                if success:
                    self._last_state = recommended_state

        except Exception as err:
            _LOGGER.error("Error in automation check: %s", err)

    def _get_charge_power(self) -> int:
        """Get the charging power based on configuration."""
        return 800

    def _get_discharge_power(self) -> int:
        """Get the discharging power based on configuration."""
        return 800

    def set_soc_limits(self, min_soc: int, max_soc: int) -> None:
        """Set SOC limits for charging/discharging."""
        self._min_soc = max(0, min(min_soc, 100))
        self._max_soc = max(0, min(max_soc, 100))
        _LOGGER.debug("SOC limits set: min=%d%%, max=%d%%", self._min_soc, self._max_soc)

    @callback
    def async_on_coordinator_update(self) -> None:
        """Handle coordinator data update."""
        if self._mode == MODE_AUTO:
            async_call_later(self.hass, 1, self._async_check_and_update)
