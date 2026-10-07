from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AskachargeConfigEntry
from .entity import AskachargeEntity


async def async_setup_entry(hass: HomeAssistant, entry: AskachargeConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        e for cp_id in coordinator.data
        for e in (OnlineSensor(coordinator, cp_id, "online"), ChargingSensor(coordinator, cp_id, "charging"))
    )


class OnlineSensor(AskachargeEntity, BinarySensorEntity):
    """WebSocket open right now. Not the same as the OCPP status, which is the last one reported."""
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool:
        return bool(self.cp.get("online"))


class ChargingSensor(AskachargeEntity, BinarySensorEntity):
    """A session is open on askacharge.com for this charger."""
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def is_on(self) -> bool:
        return self.cp.get("active_session") is not None
