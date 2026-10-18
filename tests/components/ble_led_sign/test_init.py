"""Test component setup, unload, and reload lifecycles."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_led_sign.const import DOMAIN
from custom_components.ble_led_sign.services import SERVICE_NAMES


async def test_setup_and_unload(
    hass: HomeAssistant, loaded_entry: MockConfigEntry
) -> None:
    """Test full setup, registry population, and clean unload."""
    assert loaded_entry.state is ConfigEntryState.LOADED
    assert loaded_entry.entry_id in hass.data[DOMAIN]

    # Check services are registered
    for service_name in SERVICE_NAMES:
        assert hass.services.has_service(DOMAIN, service_name)

    # Check entity registry has entries
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, loaded_entry.entry_id)
    assert len(entries) > 0

    # Unload entry
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()

    assert loaded_entry.state is ConfigEntryState.NOT_LOADED
    assert loaded_entry.entry_id not in hass.data.get(DOMAIN, {})

    # Since all entries unloaded, services should be removed
    for service_name in SERVICE_NAMES:
        assert not hass.services.has_service(DOMAIN, service_name)


async def test_reload_entry(hass: HomeAssistant, loaded_entry: MockConfigEntry) -> None:
    """Test reloading the config entry."""
    assert loaded_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_reload(loaded_entry.entry_id)
    await hass.async_block_till_done()

    assert loaded_entry.state is ConfigEntryState.LOADED
    assert loaded_entry.entry_id in hass.data[DOMAIN]


async def test_failed_platform_setup_rolls_back(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    advertisement: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test platform setup failure rolls back cleanly."""

    async def fail_forward(*_args, **_kwargs):
        raise RuntimeError("simulated platform load failure")

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", fail_forward)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    assert not hass.services.has_service(DOMAIN, "write")
    assert not hass.services.has_service(DOMAIN, "send_text")
    assert not hass.services.has_service(DOMAIN, "send_command")


async def test_multi_entry_service_cleanup(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    loaded_ipixel_entry: MockConfigEntry,
) -> None:
    """Test that services remain when one entry is unloaded and removed when both are."""
    assert hass.services.has_service(DOMAIN, "write")

    # Unload first entry
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()

    # Second entry is still loaded, services must remain
    assert hass.services.has_service(DOMAIN, "write")

    # Unload second entry
    assert await hass.config_entries.async_unload(loaded_ipixel_entry.entry_id)
    await hass.async_block_till_done()

    # Now all services should be removed
    for service_name in SERVICE_NAMES:
        assert not hass.services.has_service(DOMAIN, service_name)
