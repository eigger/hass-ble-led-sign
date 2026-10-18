"""Test BLE LED Sign light platform."""

from __future__ import annotations

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_light_turn_on_and_off(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test light turn on, set brightness/effect, and turn off."""
    state = hass.states.get("light.ble_led_sign_ccddeeff_display_power")
    assert state is not None
    assert state.state == "on"

    transport.clear()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_off",
        {ATTR_ENTITY_ID: "light.ble_led_sign_ccddeeff_display_power"},
        blocking=True,
    )
    assert len(transport.writes) > 0
    state = hass.states.get("light.ble_led_sign_ccddeeff_display_power")
    assert state.state == "off"

    transport.clear()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_ENTITY_ID: "light.ble_led_sign_ccddeeff_display_power",
            "brightness": 200,
            "effect": "left",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0
    state = hass.states.get("light.ble_led_sign_ccddeeff_display_power")
    assert state.state == "on"
    assert state.attributes["brightness"] == 200
    assert state.attributes["effect"] == "left"
