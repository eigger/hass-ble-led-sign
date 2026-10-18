"""Test BLE LED Sign text platform."""

from __future__ import annotations

from homeassistant.components.text import DOMAIN as TEXT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_text_scroll_text(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test updating scroll text entity."""
    state = hass.states.get("text.ble_led_sign_ccddeeff_scroll_text")
    assert state is not None

    transport.clear()
    await hass.services.async_call(
        TEXT_DOMAIN,
        "set_value",
        {
            ATTR_ENTITY_ID: "text.ble_led_sign_ccddeeff_scroll_text",
            "value": "Test Notice",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0
    state = hass.states.get("text.ble_led_sign_ccddeeff_scroll_text")
    assert state.state == "Test Notice"
