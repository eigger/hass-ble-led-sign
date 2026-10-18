"""Test BLE LED Sign image platform."""

from __future__ import annotations

import io

from homeassistant.core import HomeAssistant
from PIL import Image
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_led_sign.const import DOMAIN

from .conftest import BleakTransport


async def test_image_entities(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test image entities for last sent display and render preview."""
    # Verify image entities are registered and available
    last_sent_state = hass.states.get("image.ble_led_sign_ccddeeff_last_sent_display")
    preview_state = hass.states.get("image.ble_led_sign_ccddeeff_render_preview")

    assert last_sent_state is not None
    assert preview_state is not None
    assert last_sent_state.state != "unavailable"
    assert preview_state.state != "unavailable"

    # Call write service with dry_run to update preview only
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    await hass.services.async_call(
        DOMAIN,
        "write",
        {
            "device_id": device_id,
            "payload": [
                {
                    "type": "rectangle",
                    "x_start": 0,
                    "y_start": 0,
                    "x_end": 10,
                    "y_end": 10,
                    "fill": "red",
                }
            ],
            "dry_run": True,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    preview_coordinator = hass.data[DOMAIN][loaded_entry.entry_id][
        "preview_coordinator"
    ]
    assert preview_coordinator.data is not None
    with Image.open(io.BytesIO(preview_coordinator.data)) as img:
        assert img.format == "PNG"

    # Call write service without dry_run to update last sent display as well
    await hass.services.async_call(
        DOMAIN,
        "write",
        {
            "device_id": device_id,
            "payload": [
                {
                    "type": "rectangle",
                    "x_start": 0,
                    "y_start": 0,
                    "x_end": 10,
                    "y_end": 10,
                    "fill": "green",
                }
            ],
            "dry_run": False,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    image_coordinator = hass.data[DOMAIN][loaded_entry.entry_id]["image_coordinator"]
    assert image_coordinator.data is not None
    with Image.open(io.BytesIO(image_coordinator.data)) as img:
        assert img.format == "PNG"
