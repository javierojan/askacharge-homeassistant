"""Polls askacharge.com every 30 seconds with a single request for all chargers."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AskachargeApi, AskachargeAuthError, AskachargeError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AskachargeCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Data is keyed by the charger's API id (UUID), which never changes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: AskachargeApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            chargers = await self.api.live()
        except AskachargeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AskachargeError as err:
            raise UpdateFailed(str(err)) from err
        return {c["id"]: c for c in chargers}
