"""Tibber API client for fetching electricity prices."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp

from .const import TIBBER_API_ENDPOINT, RESOLUTION_HOURLY, RESOLUTION_QUARTERLY

_LOGGER = logging.getLogger(__name__)


# GraphQL Queries
HOMES_QUERY = """
{
  viewer {
    homes {
      id
      appNickname
      address {
        address1
        postalCode
        city
      }
      currentSubscription {
        status
      }
    }
  }
}
"""

PRICE_QUERY_TEMPLATE = """
{{
  viewer {{
    home(id: "{home_id}") {{
      currentSubscription {{
        priceInfo{resolution_param} {{
          current {{
            startsAt
            total
            energy
            tax
            currency
            level
          }}
          today {{
            startsAt
            total
            energy
            tax
            currency
            level
          }}
          tomorrow {{
            startsAt
            total
            energy
            tax
            currency
            level
          }}
        }}
      }}
    }}
  }}
}}
"""


class TibberApiClient:
    """Client for Tibber GraphQL API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str,
        home_id: str | None = None,
    ) -> None:
        """Initialize the Tibber API client."""
        self._session = session
        self._token = token
        self._home_id = home_id
        self._homes: list[dict[str, Any]] = []

    @property
    def home_id(self) -> str | None:
        """Return the home ID."""
        return self._home_id

    @home_id.setter
    def home_id(self, value: str) -> None:
        """Set the home ID."""
        self._home_id = value

    async def _async_execute_query(self, query: str) -> dict[str, Any] | None:
        """Execute a GraphQL query."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        payload = {"query": query}

        try:
            async with self._session.post(
                TIBBER_API_ENDPOINT,
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Tibber API error: %s - %s",
                        response.status,
                        await response.text(),
                    )
                    return None

                data = await response.json()

                if "errors" in data:
                    _LOGGER.error("Tibber GraphQL errors: %s", data["errors"])
                    return None

                return data.get("data")

        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Tibber API: %s", err)
            return None

    async def async_verify_connection(self) -> bool:
        """Verify the API connection and token."""
        data = await self._async_execute_query(HOMES_QUERY)
        if data and "viewer" in data and "homes" in data["viewer"]:
            self._homes = data["viewer"]["homes"]
            return len(self._homes) > 0
        return False

    async def async_get_homes(self) -> list[dict[str, Any]]:
        """Get list of homes associated with the account."""
        if not self._homes:
            await self.async_verify_connection()
        return self._homes

    async def async_get_prices(
        self,
        resolution: str = RESOLUTION_HOURLY,
    ) -> dict[str, Any] | None:
        """Fetch current, today's and tomorrow's prices.

        Args:
            resolution: Price resolution (HOURLY or QUARTER_HOURLY)

        Returns:
            Dictionary with price data or None on error
        """
        if not self._home_id:
            _LOGGER.error("No home ID configured")
            return None

        # Build resolution parameter
        resolution_param = ""
        if resolution == RESOLUTION_QUARTERLY:
            resolution_param = "(resolution: QUARTER_HOURLY)"

        query = PRICE_QUERY_TEMPLATE.format(
            home_id=self._home_id,
            resolution_param=resolution_param,
        )

        data = await self._async_execute_query(query)

        if not data:
            return None

        try:
            price_info = data["viewer"]["home"]["currentSubscription"]["priceInfo"]
            return self._normalize_price_data(price_info)
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing price data: %s", err)
            return None

    def _normalize_price_data(self, price_info: dict[str, Any]) -> dict[str, Any]:
        """Normalize Tibber price data to internal format.

        Converts Tibber format to a consistent internal format similar to Nord Pool.
        """
        result = {
            "current": None,
            "today": [],
            "tomorrow": [],
            "tomorrow_valid": False,
            "currency": "EUR",
        }

        # Process current price
        if price_info.get("current"):
            current = price_info["current"]
            result["current"] = {
                "start": current["startsAt"],
                "value": current["total"],
                "energy": current.get("energy"),
                "tax": current.get("tax"),
                "level": current.get("level"),
            }
            result["currency"] = current.get("currency", "EUR")

        # Process today's prices
        if price_info.get("today"):
            result["today"] = [
                {
                    "start": p["startsAt"],
                    "value": p["total"],
                    "energy": p.get("energy"),
                    "tax": p.get("tax"),
                    "level": p.get("level"),
                }
                for p in price_info["today"]
            ]

        # Process tomorrow's prices
        if price_info.get("tomorrow") and len(price_info["tomorrow"]) > 0:
            result["tomorrow"] = [
                {
                    "start": p["startsAt"],
                    "value": p["total"],
                    "energy": p.get("energy"),
                    "tax": p.get("tax"),
                    "level": p.get("level"),
                }
                for p in price_info["tomorrow"]
            ]
            result["tomorrow_valid"] = True

        return result
