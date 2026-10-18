"""Test BLE LED Sign switch platform."""

from __future__ import annotations

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import BleakTransport


async def test_switch_flip(
    hass: HomeAssistant,
    loaded_ipixel_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test display flip switch on iPixel Color device."""
    # Find the flip switch entity
    switches = [s for s in hass.states.async_entity_ids("switch") if "_flip" in s]
    assert len(switches) == 1
    entity_id = switches[0]

    transport.clear()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(transport.writes) > 0
    assert hass.states.get(entity_id).state == "on"

    transport.clear()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert len(transport.writes) > 0
    assert hass.states.get(entity_id).state == "off"
