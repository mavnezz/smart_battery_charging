"""Config flow for Smart Battery Charging integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_TIBBER_TOKEN,
    CONF_HOME_ID,
    CONF_PRICE_RESOLUTION,
    CONF_CHARGE_WINDOWS,
    CONF_DISCHARGE_WINDOWS,
    CONF_CHEAP_PERCENTILE,
    CONF_EXPENSIVE_PERCENTILE,
    CONF_MIN_SPREAD,
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_EFFICIENCY,
    CONF_ZENDURE_DEVICE_ID,
    RESOLUTION_HOURLY,
    RESOLUTION_QUARTERLY,
    DEFAULT_CHARGE_WINDOWS,
    DEFAULT_DISCHARGE_WINDOWS,
    DEFAULT_CHEAP_PERCENTILE,
    DEFAULT_EXPENSIVE_PERCENTILE,
    DEFAULT_MIN_SPREAD,
    DEFAULT_BATTERY_EFFICIENCY,
)
from .tibber_api import TibberApiClient

_LOGGER = logging.getLogger(__name__)


class SmartBatteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Battery Charging."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._tibber_token: str | None = None
        self._homes: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - Tibber token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._tibber_token = user_input[CONF_TIBBER_TOKEN]

            # Validate token and get homes
            session = async_get_clientsession(self.hass)
            client = TibberApiClient(session=session, token=self._tibber_token)

            if await client.async_verify_connection():
                self._homes = await client.async_get_homes()

                if len(self._homes) == 1:
                    # Only one home, use it directly
                    return self.async_create_entry(
                        title=self._homes[0].get("appNickname", "Smart Battery Charging"),
                        data={
                            CONF_TIBBER_TOKEN: self._tibber_token,
                            CONF_HOME_ID: self._homes[0]["id"],
                        },
                    )
                elif len(self._homes) > 1:
                    # Multiple homes, let user choose
                    return await self.async_step_select_home()
                else:
                    errors["base"] = "no_homes"
            else:
                errors["base"] = "invalid_token"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TIBBER_TOKEN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "token_url": "https://developer.tibber.com/settings/access-token"
            },
        )

    async def async_step_select_home(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle home selection when multiple homes exist."""
        if user_input is not None:
            home_id = user_input[CONF_HOME_ID]

            # Find selected home for title
            selected_home = next(
                (h for h in self._homes if h["id"] == home_id),
                self._homes[0],
            )

            return self.async_create_entry(
                title=selected_home.get("appNickname", "Smart Battery Charging"),
                data={
                    CONF_TIBBER_TOKEN: self._tibber_token,
                    CONF_HOME_ID: home_id,
                },
            )

        # Build home selection
        home_options = {
            home["id"]: f"{home.get('appNickname', 'Home')} ({home.get('address', {}).get('address1', '')})"
            for home in self._homes
        }

        return self.async_show_form(
            step_id="select_home",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOME_ID): vol.In(home_options),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SmartBatteryOptionsFlow:
        """Get the options flow for this handler."""
        return SmartBatteryOptionsFlow()


class SmartBatteryOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Battery Charging."""

    def _find_zendure_devices(self) -> dict[str, str]:
        """Find all Zendure devices in Home Assistant."""
        devices: dict[str, str] = {"": "-- Kein Gerät --"}

        try:
            # Search all states for Zendure entities
            all_states = self.hass.states.async_all()
            seen_devices: set[str] = set()

            for state in all_states:
                entity_id = state.entity_id
                if "zendure" in entity_id.lower():
                    # Extract device name from entity_id
                    parts = entity_id.split(".")
                    if len(parts) >= 2:
                        entity_name = parts[1]
                        # Try to extract base device name
                        # Remove common prefixes and suffixes
                        if entity_name.startswith("zendure_"):
                            entity_name = entity_name[8:]  # Remove "zendure_"

                        # Find the device base name by looking for known patterns
                        base_name = entity_name
                        for suffix in ["_electric_level", "_battery_level", "_output_power",
                                      "_input_power", "_solar_power", "_pack_power",
                                      "_ac_mode", "_bypass_mode", "_state", "_soc",
                                      "_charge_power", "_discharge_power", "_grid_power"]:
                            if entity_name.endswith(suffix):
                                base_name = entity_name[:-len(suffix)]
                                break

                        if base_name and base_name not in seen_devices:
                            seen_devices.add(base_name)
                            friendly_name = state.attributes.get("friendly_name", base_name)
                            # Clean up friendly name
                            for remove in ["Electric Level", "Battery Level", "Output Power",
                                          "Input Power", "Solar Power", "AC Mode"]:
                                friendly_name = friendly_name.replace(remove, "").strip()
                            if not friendly_name:
                                friendly_name = base_name.replace("_", " ").title()
                            devices[base_name] = friendly_name

        except Exception as err:
            _LOGGER.error("Error finding Zendure devices: %s", err)

        return devices

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        # Find available Zendure devices
        zendure_devices = self._find_zendure_devices()
        current_device = options.get(CONF_ZENDURE_DEVICE_ID, "")

        # If current device not in list, add it
        if current_device and current_device not in zendure_devices:
            zendure_devices[current_device] = current_device

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ZENDURE_DEVICE_ID,
                        default=current_device,
                    ): vol.In(zendure_devices),
                    vol.Optional(
                        CONF_PRICE_RESOLUTION,
                        default=options.get(CONF_PRICE_RESOLUTION, RESOLUTION_HOURLY),
                    ): vol.In(
                        {
                            RESOLUTION_HOURLY: "Stündlich (24 Fenster/Tag)",
                            RESOLUTION_QUARTERLY: "15 Minuten (96 Fenster/Tag)",
                        }
                    ),
                    vol.Optional(
                        CONF_CHARGE_WINDOWS,
                        default=options.get(CONF_CHARGE_WINDOWS, DEFAULT_CHARGE_WINDOWS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                    vol.Optional(
                        CONF_DISCHARGE_WINDOWS,
                        default=options.get(CONF_DISCHARGE_WINDOWS, DEFAULT_DISCHARGE_WINDOWS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                    vol.Optional(
                        CONF_CHEAP_PERCENTILE,
                        default=options.get(CONF_CHEAP_PERCENTILE, DEFAULT_CHEAP_PERCENTILE),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                    vol.Optional(
                        CONF_EXPENSIVE_PERCENTILE,
                        default=options.get(CONF_EXPENSIVE_PERCENTILE, DEFAULT_EXPENSIVE_PERCENTILE),
                    ): vol.All(vol.Coerce(int), vol.Range(min=50, max=99)),
                    vol.Optional(
                        CONF_MIN_SPREAD,
                        default=options.get(CONF_MIN_SPREAD, DEFAULT_MIN_SPREAD),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
                    vol.Optional(
                        CONF_BATTERY_CAPACITY,
                        default=options.get(CONF_BATTERY_CAPACITY, 0.8),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
                    vol.Optional(
                        CONF_BATTERY_EFFICIENCY,
                        default=options.get(CONF_BATTERY_EFFICIENCY, DEFAULT_BATTERY_EFFICIENCY),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=1.0)),
                }
            ),
        )
