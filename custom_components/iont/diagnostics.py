"""Diagnostics support for the IONT integration."""

from typing import Any

from pyiont import IontError

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import IontConfigEntry

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: IontConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The raw register map is what an issue about a wrong reading needs: every
    register the integration reads, as the charger returned it.
    """
    coordinator = entry.runtime_data

    registers: dict[str, Any]
    try:
        registers = await coordinator.charger.async_read_raw()
    except IontError as err:
        registers = {"error": str(err)}

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "connector_count": coordinator.charger.connector_count,
        "updated": sorted(coordinator.data.updated),
        "failed": {name: str(err) for name, err in coordinator.data.failed.items()},
        "registers": registers,
    }
