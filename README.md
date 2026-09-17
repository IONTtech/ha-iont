# IONT for Home Assistant

Home Assistant integration for [IONT](https://iont.tech) EV chargers over
Modbus TCP, on your local network. No account, no cloud.

This is the HACS (custom integration) distribution. The same integration is
being submitted to Home Assistant Core; once it is merged there, Home
Assistant will offer to switch you over automatically, since both use the
domain `iont`.

## Requirements

- Home Assistant **2026.9.0** or newer (it reuses the shared Modbus connection
  of Home Assistant's built-in `modbus` integration).
- Modbus TCP enabled on the charger, in its administration interface under
  **Protocols**. To control charging from Home Assistant (authorization, boost,
  power limit), also enable writing there; reading alone is enough for the
  sensors. The charger listens on port `502`.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Top-right menu → **Custom repositories**.
3. Repository: `https://github.com/IONTtech/ha-iont`, type **Integration**, then **Add**.
4. Open the new **IONT** entry and select **Download**.
5. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=IONTtech&repository=ha-iont&category=integration)

### Manual

Copy `custom_components/iont` into your Home Assistant `config/custom_components`
directory and restart.

## Configuration

1. **Settings → Devices & services → Add integration → IONT**.
2. Enter the charger's hostname or IP address (port `502` by default).

The charger is added as a device, with each connector as a device beneath it.

## What you get

- **Charger**: available power, status, charging strategy, power limits;
  free-charging state; an **External power limit** number for a home energy
  manager.
- **Each connector**: charging state, vehicle state, power, session / last
  session / lifetime energy, per-phase current (voltage, frequency, limits and
  temperatures available but disabled by default), battery state of charge for
  DC connectors; charging / authorized / vehicle-connected / problem /
  connectivity binary sensors; a **Charging authorization** switch and, where
  the charger assigns a connector ID, a **Boost charging** button.
- **Diagnostics** download with the raw register map (the charger's address is
  redacted).

## Support

Issues: <https://github.com/IONTtech/ha-iont/issues>

## License

MIT
