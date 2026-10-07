# askacharge.com for Home Assistant

Your OCPP chargers managed on [askacharge.com](https://askacharge.com), in Home Assistant: status,
session energy and power, and a switch to start and stop charging.

This is **not** an OCPP server. Your chargers stay connected to askacharge.com (billing, RFID cards,
QR payments, roaming keep working) and Home Assistant reads them through the askacharge.com API.
If you want Home Assistant itself to be the OCPP server, use the
[OCPP integration](https://github.com/lbbrhzn/ocpp) instead: a charger talks to one server at a time.

Step-by-step guide with automation examples: [English](https://askacharge.com/askacharge/en/blog/home-assistant-ev-charger.html) · [Español](https://askacharge.com/askacharge/blog/cargadores-home-assistant.html).

## What you get

One device per charger, with:

| Entity | What it is |
|---|---|
| `sensor.<charger>_status` | OCPP status: available, charging, suspended by vehicle, faulted… |
| `sensor.<charger>_session_energy` | kWh of the session in progress (0 when idle). Works with the Energy dashboard |
| `sensor.<charger>_power` | kW of the session in progress, from the charger's `Power.Active.Import` readings |
| `sensor.<charger>_session_duration` / `_session_start` | Of the session in progress |
| `binary_sensor.<charger>_online` | The charger's WebSocket is open right now |
| `binary_sensor.<charger>_charging` | A session is open |
| `switch.<charger>_charge` | On = remote start, off = remote stop |
| `sensor.<charger>_last_heartbeat` | Disabled by default |

Data refreshes every 30 seconds with a single request for all chargers.

## Install

**HACS:** HACS → ⋮ → Custom repositories → `https://github.com/javierojan/askacharge-homeassistant`,
category *Integration*. Install *askacharge.com* and restart Home Assistant.

**Manual:** copy `custom_components/askacharge` into your `config/custom_components/` and restart.

Then *Settings → Devices & services → Add integration → askacharge.com*.

## The API key

Create it in the askacharge.com panel, **API Keys** menu, with:

- **Sessions → read** (required): status and sessions.
- **OCPP commands → Start charge** and **Stop charge** (optional): only if you want the switch to work.
  Without them the switch returns an error and nothing else changes.

Do not limit the key to a location: the live view covers every charger of the brand, and a
location-limited key is refused there. Every write the key makes is recorded in the panel's API key
activity log.

## Good to know

- Starting from Home Assistant uses your brand's **PANEL** card, the same as the Start button in the
  panel. The session is billed with the tariff that card has.
- The switch follows the real session: after you turn it on, it turns on when the charger actually
  starts (a few seconds), not before. A charger that is offline shows the switch as unavailable.
- Power and energy come from the charger's meter readings. A charger that sends readings every
  15 minutes updates every 15 minutes (askacharge.com sets 60 s on boot when it can).

## Support

Open an issue here or write to info@askacharge.com.

---

### En castellano

Integración de Home Assistant para los cargadores gestionados en askacharge.com: estado, energía y
potencia de la sesión en curso, y un interruptor para arrancar y parar. Se instala desde HACS como
repositorio personalizado y se configura con una API key del panel (menú *API Keys*, permiso
*Sesiones → leer* y, para el interruptor, *Comandos OCPP → Arrancar carga* y *Parar carga*).
