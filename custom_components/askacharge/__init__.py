"""askacharge.com: OCPP chargers managed on askacharge.com, in Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AskachargeApi
from .const import CONF_BASE_URL, DEFAULT_BASE_URL
from .coordinator import AskachargeCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]

type AskachargeConfigEntry = ConfigEntry[AskachargeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AskachargeConfigEntry) -> bool:
    api = AskachargeApi(async_get_clientsession(hass), entry.data[CONF_API_KEY],
                        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL))
    coordinator = AskachargeCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AskachargeConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
