"""Test BLE LED Sign custom services."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_led_sign.const import DOMAIN

from .conftest import BleakTransport


async def test_service_write(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test calling the write service with imagespec payload."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

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
        },
        blocking=True,
    )

    assert len(transport.writes) > 0


async def test_service_write_dry_run(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test write service with dry_run=True generates preview but does not send BLE packets."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

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
                    "x_end": 5,
                    "y_end": 5,
                    "fill": "blue",
                }
            ],
            "dry_run": True,
        },
        blocking=True,
    )

    # In dry_run, no BLE packets must be sent
    assert len(transport.writes) == 0


async def test_service_send_text(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test send_text service."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

    await hass.services.async_call(
        DOMAIN,
        "send_text",
        {
            "device_id": device_id,
            "text": "Hello Home Assistant",
        },
        blocking=True,
    )

    assert len(transport.writes) > 0


async def test_service_send_command(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test send_command service."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

    await hass.services.async_call(
        DOMAIN,
        "send_command",
        {
            "device_id": device_id,
            "command": "brightness",
            "value": 100,
        },
        blocking=True,
    )

    assert len(transport.writes) > 0


async def test_service_set_icon(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test set_icon service."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

    await hass.services.async_call(
        DOMAIN,
        "set_icon",
        {
            "device_id": device_id,
            "icon_id": 1,
        },
        blocking=True,
    )

    assert len(transport.writes) > 0


async def test_service_set_music(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test set_music service."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()

    await hass.services.async_call(
        DOMAIN,
        "set_music",
        {
            "device_id": device_id,
            "heights": [1, 2, 3, 4, 5, 6, 7, 8],
            "colors": [1, 1, 2, 2, 1, 1, 2, 2],
        },
        blocking=True,
    )

    assert len(transport.writes) > 0


async def test_service_missing_device_id_raises(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
) -> None:
    """Test calling service without device_id raises HomeAssistantError."""
    with pytest.raises(HomeAssistantError, match="device_id is required"):
        await hass.services.async_call(
            DOMAIN,
            "send_text",
            {"text": "Test"},
            blocking=True,
        )


async def test_service_unknown_device_id_raises(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
) -> None:
    """Test calling service with non-existent device_id raises HomeAssistantError."""
    with pytest.raises(HomeAssistantError, match="No BLE LED Sign entry found"):
        await hass.services.async_call(
            DOMAIN,
            "send_text",
            {"device_id": "nonexistent_device_id", "text": "Test"},
            blocking=True,
        )


async def test_service_target_entity_id(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test calling service targeting entity_id resolves correctly to entry."""
    from homeassistant.helpers import entity_registry as er

    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, loaded_entry.entry_id)
    sign_entity = next(e for e in entries if e.domain == "light")

    transport.clear()
    await hass.services.async_call(
        DOMAIN,
        "send_text",
        {
            "entity_id": sign_entity.entity_id,
            "text": "Hello Entity",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0


async def test_service_target_mixed_area(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test calling service targeting an area with mixed entities only targets ble_led_sign."""
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import entity_registry as er

    area_reg = ar.async_get(hass)
    area = area_reg.async_create("living_room")

    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, loaded_entry.entry_id)
    sign_entity = next(e for e in entries if e.domain == "light")
    ent_reg.async_update_entity(sign_entity.entity_id, area_id=area.id)

    # Add an unrelated entity from another integration to the same area
    unrelated = ent_reg.async_get_or_create(
        domain="light",
        platform="other_domain",
        unique_id="other_x1",
    )
    ent_reg.async_update_entity(unrelated.entity_id, area_id=area.id)

    transport.clear()
    await hass.services.async_call(
        DOMAIN,
        "send_text",
        {
            "area_id": area.id,
            "text": "Area Message",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0


async def test_service_target_group(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Test calling service targeting a group expands correctly."""
    from homeassistant.const import ATTR_ENTITY_ID
    from homeassistant.helpers import entity_registry as er

    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, loaded_entry.entry_id)
    sign_entity = next(e for e in entries if e.domain == "light")

    hass.states.async_set(
        "group.signs",
        "on",
        {ATTR_ENTITY_ID: [sign_entity.entity_id]},
    )

    transport.clear()
    await hass.services.async_call(
        DOMAIN,
        "send_text",
        {
            "entity_id": "group.signs",
            "text": "Group Message",
        },
        blocking=True,
    )
    assert len(transport.writes) > 0


async def test_service_target_invalid_entity_id_raises(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
) -> None:
    """Test calling service targeting an invalid or other integration entity raises HomeAssistantError."""
    # Nonexistent entity
    with pytest.raises(HomeAssistantError, match="not a valid ble_led_sign entity"):
        await hass.services.async_call(
            DOMAIN,
            "send_text",
            {
                "entity_id": "light.nonexistent_entity",
                "text": "Test",
            },
            blocking=True,
        )

    # Entity from another integration
    from homeassistant.helpers import entity_registry as er

    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get_or_create(
        domain="light",
        platform="other_domain",
        unique_id="other_1234",
    )
    with pytest.raises(HomeAssistantError, match="not a valid ble_led_sign entity"):
        await hass.services.async_call(
            DOMAIN,
            "send_text",
            {
                "entity_id": entry.entity_id,
                "text": "Test",
            },
            blocking=True,
        )


async def test_write_schema_preserves_legacy_data_formats(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    transport: BleakTransport,
) -> None:
    """Schema registration retains RGB backgrounds, truthy dry-run and extra fields."""
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    transport.clear()
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
                    "x_end": 5,
                    "y_end": 5,
                    "fill": "white",
                }
            ],
            "background": (0, 0, 0),
            "rotate": "0",
            "dry_run": 1,
            "legacy_extra": "preserved",
        },
        blocking=True,
    )
    assert not transport.writes
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    assert runtime["preview_coordinator"].data is not None
