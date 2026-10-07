"""Charging switch: on = RemoteStart (with the brand's PANEL card), off = RemoteStop.

The command only returns the charger's acknowledgement; the real start or stop arrives later over
OCPP, so the state follows the next refresh instead of being set optimistically.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AskachargeConfigEntry
from .api import AskachargeError
from .entity import AskachargeEntity


async def async_setup_entry(hass: HomeAssistant, entry: AskachargeConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ChargeSwitch(coordinator, cp_id, "charge") for cp_id in coordinator.data)


class ChargeSwitch(AskachargeEntity, SwitchEntity):
    @property
    def is_on(self) -> bool:
        return self.cp.get("active_session") is not None

    @property
    def available(self) -> bool:
        return super().available and bool(self.cp.get("online")) and not self.cp.get("pending_auth")

    async def _comando(self, coro) -> None:
        try:
            r = await coro
        except AskachargeError as err:
            raise HomeAssistantError(f"askacharge.com: {err}") from err
        if str(r.get("status", "")).lower() == "rejected":
            raise HomeAssistantError(f"{self.cp['charge_point_id']} rejected the command")
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._comando(self.coordinator.api.start(self.cp["charge_point_id"]))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._comando(self.coordinator.api.stop(self.cp["charge_point_id"]))
