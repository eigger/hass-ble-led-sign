"""Export real session reports without configuration credentials."""

import json

from custom_components.ble_led_sign.const import DOMAIN
from custom_components.ble_led_sign.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_exports_only_runtime_reports(hass, loaded_entry):
    """Diagnostic downloads omit entry identity and arbitrary configuration secrets."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    await hass.services.async_call(
        DOMAIN,
        "send_text",
        {"device_id": device_id, "text": "private sign text"},
        blocking=True,
    )
    result = await async_get_config_entry_diagnostics(hass, loaded_entry)
    assert result["driver"] == "coolled"
    assert result["last"]["success"] is True
    assert result["failures"] == 0
    serialized = json.dumps(result, default=str)
    assert loaded_entry.unique_id not in serialized
    assert "private sign text" not in serialized
    assert "password" not in result
