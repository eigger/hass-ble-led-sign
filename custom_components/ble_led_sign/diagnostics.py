"""Download BLE session diagnostics without credentials or radio identities."""

from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN

_REDACT = {
    "via",
    "advertised_via",
    "error",
    "disconnect_error",
    "stale_close_error",
    "likely_cause",
}


async def async_get_config_entry_diagnostics(hass, entry):
    """Expose frozen reports, never entry data, passwords or sign content."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    reports = runtime["reports"]
    return async_redact_data(
        {
            "driver": entry.data.get("driver_id"),
            "connected": runtime["connected"],
            "failures": reports.failures,
            "last": reports.last,
            "last_failure": reports.last_failure,
            "last_retry": reports.last_retry,
        },
        _REDACT,
    )
