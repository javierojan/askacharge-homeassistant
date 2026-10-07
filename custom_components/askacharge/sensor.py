from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import AskachargeConfigEntry
from .const import STATUSES
from .entity import AskachargeEntity


async def async_setup_entry(hass: HomeAssistant, entry: AskachargeConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        e for cp_id in coordinator.data
        for e in (StatusSensor(coordinator, cp_id, "status"),
                  SessionEnergySensor(coordinator, cp_id, "session_energy"),
                  PowerSensor(coordinator, cp_id, "power"),
                  SessionDurationSensor(coordinator, cp_id, "session_duration"),
                  SessionStartSensor(coordinator, cp_id, "session_start"),
                  LastHeartbeatSensor(coordinator, cp_id, "last_heartbeat"))
    )


def _fecha(valor: str | None) -> datetime | None:
    # askacharge.com sends naive UTC ISO timestamps
    if not valor:
        return None
    d = dt_util.parse_datetime(valor)
    if d is None:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt_util.UTC)


class StatusSensor(AskachargeEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES

    @property
    def native_value(self) -> str:
        estado = (self.cp.get("status") or "unknown").lower()
        return estado if estado in STATUSES else "unknown"

    @property
    def extra_state_attributes(self) -> dict:
        s = self.cp.get("active_session") or {}
        return {"charge_point_id": self.cp["charge_point_id"], "location": self.cp.get("location_name"),
                "pending_auth": self.cp.get("pending_auth"), "id_tag": s.get("id_tag"),
                "driver": s.get("client_name")}


class SessionEnergySensor(AskachargeEntity, SensorEntity):
    """Energy of the session in progress; drops to 0 when it ends (HA treats that as a meter reset)."""
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float:
        s = self.cp.get("active_session")
        return float(s["energy_kwh"]) if s else 0.0


class PowerSensor(AskachargeEntity, SensorEntity):
    """Last Power.Active.Import reading of the session in progress; 0 when idle."""
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_suggested_display_precision = 1

    @property
    def native_value(self) -> float | None:
        s = self.cp.get("active_session")
        if not s:
            return 0.0
        return s.get("power_kw")   # None (unknown) if the charger does not report power


class SessionDurationSensor(AskachargeEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self) -> int:
        s = self.cp.get("active_session")
        return int(s["duration_minutes"]) if s else 0


class SessionStartSensor(AskachargeEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        s = self.cp.get("active_session")
        return _fecha(s.get("start_time")) if s else None


class LastHeartbeatSensor(AskachargeEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> datetime | None:
        return _fecha(self.cp.get("last_heartbeat"))
