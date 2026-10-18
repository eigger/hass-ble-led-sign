"""Test BLE LED Sign button platform."""

from __future__ import annotations

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_button_clear(
    hass: HomeAssistant,
    loaded_ipixel_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test clear display button on iPixel Color device."""
    buttons = [b for b in hass.states.async_entity_ids("button") if "_clear" in b]
    assert len(buttons) == 1
    entity_id = buttons[0]

    transport.clear()
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(transport.writes) > 0


async def test_button_countdown(
    hass: HomeAssistant,
    loaded_ipixel_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test start countdown button on iPixel Color device."""
    buttons = [b for b in hass.states.async_entity_ids("button") if "countdown" in b]
    assert len(buttons) == 1
    entity_id = buttons[0]

    transport.clear()
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(transport.writes) > 0
