"""Smart Battery Charging integration for Home Assistant.

This integration optimizes battery charging/discharging based on Tibber electricity prices
and controls Zendure Solarflow battery systems.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_TIBBER_TOKEN,
    CONF_HOME_ID,
    CONF_ZENDURE_DEVICE_ID,
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import SmartBatteryCoordinator
from .tibber_api import TibberApiClient
from .battery_controller import BatteryController
from .automation_handler import AutomationHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Battery Charging from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create Tibber API client
    session = async_get_clientsession(hass)
    tibber_client = TibberApiClient(
        session=session,
        token=entry.data[CONF_TIBBER_TOKEN],
        home_id=entry.data.get(CONF_HOME_ID),
    )

    # Verify connection
    if not await tibber_client.async_verify_connection():
        _LOGGER.error("Failed to connect to Tibber API")
        return False

    # Create coordinator
    coordinator = SmartBatteryCoordinator(
        hass=hass,
        tibber_client=tibber_client,
        entry=entry,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create battery controller
    zendure_device = entry.options.get(CONF_ZENDURE_DEVICE_ID)
    battery_controller = BatteryController(
        hass=hass,
        device_name=zendure_device,
    )

    # Create automation handler
    automation_handler = AutomationHandler(
        hass=hass,
        coordinator=coordinator,
        battery_controller=battery_controller,
        entry_id=entry.entry_id,
    )

    # Register automation handler as coordinator listener
    unsub_coordinator_listener = coordinator.async_add_listener(
        automation_handler.async_on_coordinator_update
    )

    # Store coordinator, controller, and automation handler
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "tibber_client": tibber_client,
        "battery_controller": battery_controller,
        "automation_handler": automation_handler,
        "unsub_coordinator_listener": unsub_coordinator_listener,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass, entry)

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        # Unsubscribe coordinator listener
        unsub = data.get("unsub_coordinator_listener")
        if unsub:
            unsub()

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up services for the integration."""

    async def handle_set_battery_state(call: ServiceCall) -> None:
        """Handle the set_battery_state service call."""
        state = call.data.get("state")
        charge_power = call.data.get("charge_power")
        discharge_power = call.data.get("discharge_power")
        target_entry_id = call.data.get("entry_id", entry.entry_id)

        data = hass.data[DOMAIN].get(target_entry_id)
        if not data:
            _LOGGER.error("Entry %s not found", target_entry_id)
            return

        controller = data.get("battery_controller")
        if controller:
            await controller.async_set_state(
                state,
                charge_power=charge_power,
                discharge_power=discharge_power,
            )

    async def handle_recalculate(call: ServiceCall) -> None:
        """Handle the recalculate_windows service call."""
        target_entry_id = call.data.get("entry_id", entry.entry_id)

        data = hass.data[DOMAIN].get(target_entry_id)
        if not data:
            _LOGGER.error("Entry %s not found", target_entry_id)
            return

        coordinator = data.get("coordinator")
        if coordinator:
            await coordinator.async_refresh()

    # Only register services once
    if not hass.services.has_service(DOMAIN, "set_battery_state"):
        hass.services.async_register(
            DOMAIN,
            "set_battery_state",
            handle_set_battery_state,
        )

    if not hass.services.has_service(DOMAIN, "recalculate_windows"):
        hass.services.async_register(
            DOMAIN,
            "recalculate_windows",
            handle_recalculate,
        )
