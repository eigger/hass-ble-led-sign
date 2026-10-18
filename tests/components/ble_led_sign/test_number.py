"""Test BLE LED Sign number platform."""

from __future__ import annotations

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_number_scroll_speed(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test setting scroll speed number."""
    state = hass.states.get("number.ble_led_sign_ccddeeff_scroll_speed")
    assert state is not None

    transport.clear()
    await hass.services.async_call(
        NUMBER_DOMAIN,
        "set_value",
        {
            ATTR_ENTITY_ID: "number.ble_led_sign_ccddeeff_scroll_speed",
            "value": 75,
        },
        blocking=True,
    )
    assert len(transport.writes) > 0
    state = hass.states.get("number.ble_led_sign_ccddeeff_scroll_speed")
    assert float(state.state) == 75.0
