"""Config flow, entities and the charge switch against a mocked askacharge.com."""
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.askacharge.const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN

LIVE = f"{DEFAULT_BASE_URL}/brand/dashboard/live"
START = f"{DEFAULT_BASE_URL}/brand/commands/remote-start"
STOP = f"{DEFAULT_BASE_URL}/brand/commands/remote-stop"

CHARGERS = [
    {"id": "11111111-1111-1111-1111-111111111111", "charge_point_id": "GARAJE-01", "status": "Charging",
     "online": True, "pending_auth": False, "location_name": "Garaje", "last_heartbeat": "2026-10-07T17:00:00",
     "latitude": None, "longitude": None,
     "active_session": {"transaction_id": "t1", "ocpp_transaction_id": 42, "id_tag": "PANEL",
                        "client_name": "PANEL", "start_time": "2026-10-07T16:30:00",
                        "duration_minutes": 30, "energy_kwh": 5.43, "power_kw": 7.2}},
    {"id": "22222222-2222-2222-2222-222222222222", "charge_point_id": "CALLE-02", "status": "Available",
     "online": False, "pending_auth": False, "location_name": None, "last_heartbeat": None,
     "latitude": None, "longitude": None, "active_session": None},
]


async def _entry(hass, aioclient_mock):
    aioclient_mock.get(LIVE, json=CHARGERS)
    entry = MockConfigEntry(domain=DOMAIN, unique_id="abcdefabcdef",
                            data={CONF_API_KEY: "ak_test_abcdefabcdef", CONF_BASE_URL: DEFAULT_BASE_URL})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_flow_ok(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(LIVE, json=CHARGERS)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.FORM
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {CONF_API_KEY: "ak_live_123456789012"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["data"] == {CONF_API_KEY: "ak_live_123456789012", CONF_BASE_URL: DEFAULT_BASE_URL}
    # the key travels in X-Api-Key, never in the URL
    assert aioclient_mock.mock_calls[0][3]["X-Api-Key"] == "ak_live_123456789012"


@pytest.mark.parametrize(("status", "error"), [(401, "invalid_auth"), (403, "invalid_auth"), (500, "cannot_connect")])
async def test_flow_errors(hass: HomeAssistant, aioclient_mock, status, error):
    aioclient_mock.get(LIVE, status=status, text="no")
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {CONF_API_KEY: "ak_live_bad"})
    assert r["type"] is FlowResultType.FORM
    assert r["errors"] == {"base": error}


async def test_entities(hass: HomeAssistant, aioclient_mock):
    await _entry(hass, aioclient_mock)
    assert hass.states.get("sensor.garaje_01_status").state == "charging"
    assert hass.states.get("sensor.garaje_01_session_energy").state == "5.43"
    assert hass.states.get("sensor.garaje_01_session_duration").state == "30"
    assert hass.states.get("sensor.garaje_01_power").state == "7.2"
    assert hass.states.get("sensor.garaje_01_session_start").state == "2026-10-07T16:30:00+00:00"
    assert hass.states.get("binary_sensor.garaje_01_online").state == "on"
    assert hass.states.get("binary_sensor.garaje_01_charging").state == "on"
    assert hass.states.get("switch.garaje_01_charge").state == "on"

    assert hass.states.get("sensor.calle_02_status").state == "available"
    assert hass.states.get("sensor.calle_02_session_energy").state == "0.0"
    assert hass.states.get("sensor.calle_02_power").state == "0.0"
    assert hass.states.get("binary_sensor.calle_02_online").state == "off"
    # offline: the switch cannot do anything, so it is unavailable rather than misleading
    assert hass.states.get("switch.calle_02_charge").state == "unavailable"


async def test_switch_sends_commands(hass: HomeAssistant, aioclient_mock):
    await _entry(hass, aioclient_mock)
    aioclient_mock.post(STOP, json={"status": "Accepted"})
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.garaje_01_charge"}, blocking=True)
    llamada = [c for c in aioclient_mock.mock_calls if str(c[1]) == STOP][0]
    assert llamada[2] == {"charge_point_id": "GARAJE-01"}

    aioclient_mock.post(START, json={"status": "Accepted", "id_tag": "PANEL"})
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.garaje_01_charge"}, blocking=True)
    llamada = [c for c in aioclient_mock.mock_calls if str(c[1]) == START][0]
    assert llamada[2] == {"charge_point_id": "GARAJE-01", "connector_id": 1}


async def test_rejected_command_is_an_error(hass: HomeAssistant, aioclient_mock):
    await _entry(hass, aioclient_mock)
    aioclient_mock.post(START, json={"status": "Rejected", "id_tag": "PANEL"})
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.garaje_01_charge"}, blocking=True)


async def test_key_without_command_scope(hass: HomeAssistant, aioclient_mock):
    await _entry(hass, aioclient_mock)
    aioclient_mock.post(STOP, status=403, text='{"detail":"scope"}')
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.garaje_01_charge"}, blocking=True)


async def test_unload(hass: HomeAssistant, aioclient_mock):
    entry = await _entry(hass, aioclient_mock)
    assert await hass.config_entries.async_unload(entry.entry_id)
