"""Calculation engine for finding optimal charging/discharging windows."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass

from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_CHEAP_PERCENTILE,
    DEFAULT_EXPENSIVE_PERCENTILE,
    DEFAULT_MIN_SPREAD,
    DEFAULT_CHARGE_WINDOWS,
    DEFAULT_DISCHARGE_WINDOWS,
    STATE_CHARGE,
    STATE_DISCHARGE,
    STATE_IDLE,
    STATE_HOLD,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PriceWindow:
    """Represents a price window."""

    start: datetime
    end: datetime
    value: float
    level: str | None = None

    def __post_init__(self):
        """Ensure datetime objects are timezone-aware."""
        if isinstance(self.start, str):
            self.start = dt_util.parse_datetime(self.start)
        if isinstance(self.end, str):
            self.end = dt_util.parse_datetime(self.end)

    def is_active(self, now: datetime | None = None) -> bool:
        """Check if this window is currently active."""
        if now is None:
            now = dt_util.now()
        return self.start <= now < self.end

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "value": self.value,
            "level": self.level,
        }


@dataclass
class CalculationResult:
    """Result of price window calculation."""

    cheapest_windows: list[PriceWindow]
    expensive_windows: list[PriceWindow]
    recommended_state: str
    current_price: float | None
    average_price: float
    min_price: float
    max_price: float
    spread_percent: float
    potential_savings: float
    is_profitable: bool = True
    avg_charge_price: float = 0.0
    avg_discharge_price: float = 0.0
    required_spread: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for sensor attributes."""
        return {
            "cheapest_windows": [w.to_dict() for w in self.cheapest_windows],
            "expensive_windows": [w.to_dict() for w in self.expensive_windows],
            "recommended_state": self.recommended_state,
            "current_price": self.current_price,
            "average_price": round(self.average_price, 4),
            "min_price": round(self.min_price, 4),
            "max_price": round(self.max_price, 4),
            "spread_percent": round(self.spread_percent, 2),
            "potential_savings": round(self.potential_savings, 4),
            "is_profitable": self.is_profitable,
            "avg_charge_price": round(self.avg_charge_price, 4),
            "avg_discharge_price": round(self.avg_discharge_price, 4),
            "required_spread": round(self.required_spread, 2),
        }


class CalculationEngine:
    """Engine for calculating optimal charge/discharge windows."""

    def __init__(
        self,
        charge_windows: int = DEFAULT_CHARGE_WINDOWS,
        discharge_windows: int = DEFAULT_DISCHARGE_WINDOWS,
        cheap_percentile: int = DEFAULT_CHEAP_PERCENTILE,
        expensive_percentile: int = DEFAULT_EXPENSIVE_PERCENTILE,
        min_spread: float = DEFAULT_MIN_SPREAD,
        battery_efficiency: float = 0.85,
    ) -> None:
        """Initialize the calculation engine."""
        self.charge_windows = charge_windows
        self.discharge_windows = discharge_windows
        self.cheap_percentile = cheap_percentile
        self.expensive_percentile = expensive_percentile
        self.min_spread = min_spread
        self.battery_efficiency = battery_efficiency

    def calculate(
        self,
        prices_today: list[dict[str, Any]],
        prices_tomorrow: list[dict[str, Any]] | None = None,
    ) -> CalculationResult:
        """Calculate optimal charging and discharging windows.

        Args:
            prices_today: List of price data for today
            prices_tomorrow: List of price data for tomorrow (optional)

        Returns:
            CalculationResult with windows and recommendations
        """
        # Combine prices
        all_prices = list(prices_today)
        if prices_tomorrow:
            all_prices.extend(prices_tomorrow)

        if not all_prices:
            return self._empty_result()

        # Convert to PriceWindow objects
        windows = self._prices_to_windows(all_prices)

        if not windows:
            return self._empty_result()

        # Calculate statistics
        values = [w.value for w in windows]
        avg_price = sum(values) / len(values)
        min_price = min(values)
        max_price = max(values)
        spread = ((max_price - min_price) / min_price * 100) if min_price > 0 else 0

        # Find percentile thresholds
        sorted_values = sorted(values)
        cheap_threshold = self._percentile(sorted_values, self.cheap_percentile)
        expensive_threshold = self._percentile(sorted_values, self.expensive_percentile)

        # Find cheapest windows (for charging)
        cheap_windows = sorted(
            [w for w in windows if w.value <= cheap_threshold],
            key=lambda x: x.value,
        )[: self.charge_windows]

        # Find most expensive windows (for discharging)
        expensive_windows = sorted(
            [w for w in windows if w.value >= expensive_threshold],
            key=lambda x: x.value,
            reverse=True,
        )[: self.discharge_windows]

        # Determine current state recommendation
        now = dt_util.now()
        current_price = None
        recommended_state = STATE_IDLE

        # Find current price
        for window in windows:
            if window.is_active(now):
                current_price = window.value
                break

        # Check if currently in a cheap or expensive window
        in_cheap_window = any(w.is_active(now) for w in cheap_windows)
        in_expensive_window = any(w.is_active(now) for w in expensive_windows)

        if in_cheap_window:
            recommended_state = STATE_CHARGE
        elif in_expensive_window:
            recommended_state = STATE_DISCHARGE
        else:
            # Check if we are BETWEEN a past cheap window and a future expensive window.
            # Battery was charged → hold until discharge time.
            most_recent_cheap_end = None
            for w in sorted(cheap_windows, key=lambda x: x.end, reverse=True):
                if w.end <= now:
                    most_recent_cheap_end = w.end
                    break

            next_expensive_start = None
            for w in sorted(expensive_windows, key=lambda x: x.start):
                if w.start > now:
                    next_expensive_start = w.start
                    break

            if most_recent_cheap_end is not None and next_expensive_start is not None:
                recommended_state = STATE_HOLD

        # Calculate potential savings
        avg_cheap = (
            sum(w.value for w in cheap_windows) / len(cheap_windows)
            if cheap_windows
            else avg_price
        )
        avg_expensive = (
            sum(w.value for w in expensive_windows) / len(expensive_windows)
            if expensive_windows
            else avg_price
        )

        # Calculate if operation is profitable considering efficiency losses
        # Breakeven: discharge_price > charge_price / efficiency
        # Required spread for breakeven: (1 / efficiency - 1) * 100 %
        breakeven_spread = (1 / self.battery_efficiency - 1) * 100  # ~17.6% at 85% efficiency

        # Use the higher of: breakeven spread or user-configured min_spread
        required_spread = max(breakeven_spread, self.min_spread)

        # Actual spread between charge and discharge prices
        actual_spread_percent = (
            ((avg_expensive - avg_cheap) / avg_cheap * 100)
            if avg_cheap > 0
            else 0
        )

        # Check if profitable
        is_profitable = actual_spread_percent >= required_spread

        # Calculate net savings per kWh after efficiency losses
        # Savings = (discharge_price * efficiency) - charge_price
        # Or: Savings = discharge_price - (charge_price / efficiency)
        if is_profitable and avg_cheap > 0:
            # Net savings = what you get back - what you paid (accounting for losses)
            potential_savings = (avg_expensive * self.battery_efficiency) - avg_cheap
        else:
            potential_savings = 0.0
            # If not profitable, don't recommend charge/discharge/hold
            if recommended_state in (STATE_CHARGE, STATE_DISCHARGE, STATE_HOLD):
                recommended_state = STATE_IDLE
                _LOGGER.info(
                    "Operation not profitable: spread %.1f%% < required %.1f%% (breakeven=%.1f%%, min_spread=%.1f%%)",
                    actual_spread_percent,
                    required_spread,
                    breakeven_spread,
                    self.min_spread,
                )

        return CalculationResult(
            cheapest_windows=sorted(cheap_windows, key=lambda x: x.start),
            expensive_windows=sorted(expensive_windows, key=lambda x: x.start),
            recommended_state=recommended_state,
            current_price=current_price,
            average_price=avg_price,
            min_price=min_price,
            max_price=max_price,
            spread_percent=spread,
            potential_savings=potential_savings,
            is_profitable=is_profitable,
            avg_charge_price=avg_cheap,
            avg_discharge_price=avg_expensive,
            required_spread=required_spread,
        )

    def _prices_to_windows(
        self, prices: list[dict[str, Any]]
    ) -> list[PriceWindow]:
        """Convert price data to PriceWindow objects."""
        windows = []

        for price in prices:
            start = price.get("start")
            value = price.get("value")

            if start is None or value is None:
                continue

            # Parse start time
            if isinstance(start, str):
                start_dt = dt_util.parse_datetime(start)
            else:
                start_dt = start

            if start_dt is None:
                continue

            # Determine window duration based on price data
            # (1 hour for hourly, 15 min for quarterly)
            # Default to 1 hour
            end_dt = start_dt + timedelta(hours=1)

            windows.append(
                PriceWindow(
                    start=start_dt,
                    end=end_dt,
                    value=value,
                    level=price.get("level"),
                )
            )

        return windows

    def _percentile(self, sorted_values: list[float], percentile: int) -> float:
        """Calculate percentile value from sorted list."""
        if not sorted_values:
            return 0.0

        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f

        if f == c:
            return sorted_values[f]

        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)

    def _empty_result(self) -> CalculationResult:
        """Return an empty result when no data is available."""
        breakeven_spread = (1 / self.battery_efficiency - 1) * 100
        required_spread = max(breakeven_spread, self.min_spread)
        return CalculationResult(
            cheapest_windows=[],
            expensive_windows=[],
            recommended_state=STATE_IDLE,
            current_price=None,
            average_price=0.0,
            min_price=0.0,
            max_price=0.0,
            spread_percent=0.0,
            potential_savings=0.0,
            is_profitable=False,
            avg_charge_price=0.0,
            avg_discharge_price=0.0,
            required_spread=required_spread,
        )

    def get_next_window(
        self, windows: list[PriceWindow], window_type: str = "cheap"
    ) -> PriceWindow | None:
        """Get the next upcoming window of the specified type.

        Args:
            windows: List of windows to search
            window_type: "cheap" or "expensive"

        Returns:
            Next upcoming window or None
        """
        now = dt_util.now()

        future_windows = [w for w in windows if w.start > now]
        if not future_windows:
            return None

        return min(future_windows, key=lambda x: x.start)
