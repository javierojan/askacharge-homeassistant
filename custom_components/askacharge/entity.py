"""Base entity: one Home Assistant device per charger."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AskachargeCoordinator


class AskachargeEntity(CoordinatorEntity[AskachargeCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: AskachargeCoordinator, cp_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._cp_id = cp_id
        self._attr_unique_id = f"{cp_id}_{key}"
        self._attr_translation_key = key
        cp = coordinator.data[cp_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cp_id)},
            name=cp["charge_point_id"],
            manufacturer="askacharge.com",
            model="OCPP charger",
            suggested_area=cp.get("location_name") or None,
            configuration_url="https://askacharge.com/askacharge/app/charge-points",
        )

    @property
    def cp(self) -> dict[str, Any]:
        return self.coordinator.data[self._cp_id]

    @property
    def available(self) -> bool:
        # A charger removed on askacharge.com disappears from the data until HA reloads
        return super().available and self._cp_id in self.coordinator.data
