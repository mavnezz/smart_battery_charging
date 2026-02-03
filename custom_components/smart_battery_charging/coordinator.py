"""Data coordinator for Smart Battery Charging."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
    CONF_PRICE_RESOLUTION,
    CONF_CHARGE_WINDOWS,
    CONF_DISCHARGE_WINDOWS,
    CONF_CHEAP_PERCENTILE,
    CONF_EXPENSIVE_PERCENTILE,
    CONF_MIN_SPREAD,
    CONF_BATTERY_EFFICIENCY,
    RESOLUTION_HOURLY,
    DEFAULT_CHARGE_WINDOWS,
    DEFAULT_DISCHARGE_WINDOWS,
    DEFAULT_CHEAP_PERCENTILE,
    DEFAULT_EXPENSIVE_PERCENTILE,
    DEFAULT_MIN_SPREAD,
    DEFAULT_BATTERY_EFFICIENCY,
)
from .tibber_api import TibberApiClient
from .calculation_engine import CalculationEngine, CalculationResult

_LOGGER = logging.getLogger(__name__)


class SmartBatteryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Smart Battery Charging data."""

    def __init__(
        self,
        hass: HomeAssistant,
        tibber_client: TibberApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

        self.tibber_client = tibber_client
        self.entry = entry
        self._last_price_data: dict[str, Any] | None = None
        self._calculation_result: CalculationResult | None = None

        # Initialize calculation engine with config options
        self._init_calculation_engine()

    def _init_calculation_engine(self) -> None:
        """Initialize or update the calculation engine from config."""
        options = self.entry.options

        self.calculation_engine = CalculationEngine(
            charge_windows=options.get(CONF_CHARGE_WINDOWS, DEFAULT_CHARGE_WINDOWS),
            discharge_windows=options.get(CONF_DISCHARGE_WINDOWS, DEFAULT_DISCHARGE_WINDOWS),
            cheap_percentile=options.get(CONF_CHEAP_PERCENTILE, DEFAULT_CHEAP_PERCENTILE),
            expensive_percentile=options.get(CONF_EXPENSIVE_PERCENTILE, DEFAULT_EXPENSIVE_PERCENTILE),
            min_spread=options.get(CONF_MIN_SPREAD, DEFAULT_MIN_SPREAD),
            battery_efficiency=options.get(CONF_BATTERY_EFFICIENCY, DEFAULT_BATTERY_EFFICIENCY),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Tibber and calculate windows."""
        try:
            # Get price resolution from options
            resolution = self.entry.options.get(CONF_PRICE_RESOLUTION, RESOLUTION_HOURLY)

            # Fetch prices from Tibber
            price_data = await self.tibber_client.async_get_prices(resolution=resolution)

            if not price_data:
                # If fetch failed but we have cached data, use it
                if self._last_price_data:
                    _LOGGER.warning("Using cached price data after fetch failure")
                    price_data = self._last_price_data
                else:
                    raise UpdateFailed("Failed to fetch price data from Tibber")

            self._last_price_data = price_data

            # Calculate optimal windows
            self._calculation_result = self.calculation_engine.calculate(
                prices_today=price_data.get("today", []),
                prices_tomorrow=price_data.get("tomorrow", []) if price_data.get("tomorrow_valid") else None,
            )

            # Build result data
            result = {
                "prices": price_data,
                "calculation": self._calculation_result.to_dict(),
                "current": price_data.get("current"),
                "currency": price_data.get("currency", "EUR"),
                "tomorrow_valid": price_data.get("tomorrow_valid", False),
            }

            return result

        except Exception as err:
            _LOGGER.error("Error updating Smart Battery Charging data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    @property
    def calculation_result(self) -> CalculationResult | None:
        """Return the current calculation result."""
        return self._calculation_result

    @property
    def current_price(self) -> float | None:
        """Return the current electricity price."""
        if self._calculation_result:
            return self._calculation_result.current_price
        return None

    @property
    def recommended_state(self) -> str:
        """Return the recommended battery state."""
        if self._calculation_result:
            return self._calculation_result.recommended_state
        return "idle"

    def update_options(self) -> None:
        """Update calculation engine when options change."""
        self._init_calculation_engine()

        # Recalculate with new options if we have price data
        if self._last_price_data:
            self._calculation_result = self.calculation_engine.calculate(
                prices_today=self._last_price_data.get("today", []),
                prices_tomorrow=(
                    self._last_price_data.get("tomorrow", [])
                    if self._last_price_data.get("tomorrow_valid")
                    else None
                ),
            )
