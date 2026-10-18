"""Test BLE LED Sign select platform."""

from __future__ import annotations

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_select_scroll_mode(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test selecting scroll mode option."""
    state = hass.states.get("select.ble_led_sign_ccddeeff_scroll_mode")
    assert state is not None

    transport.clear()
    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {
            ATTR_ENTITY_ID: "select.ble_led_sign_ccddeeff_scroll_mode",
            "option": "right",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0
    state = hass.states.get("select.ble_led_sign_ccddeeff_scroll_mode")
    assert state.state == "right"
