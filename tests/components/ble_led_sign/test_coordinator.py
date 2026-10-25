"""Actual Bluetooth coordinator and HA unload lifetime."""

from custom_components.ble_led_sign.const import DOMAIN
from custom_components.ble_led_sign.coordinator import (
    BleLedSignPassiveBluetoothProcessorCoordinator,
)


async def test_coordinator_preserves_advertisement_and_unloads(hass, loaded_entry):
    """A real Bluetooth coordinator owns parsed device data and its entry."""
    coordinator = loaded_entry.runtime_data
    assert isinstance(coordinator, BleLedSignPassiveBluetoothProcessorCoordinator)
    assert coordinator.entry is loaded_entry
    assert coordinator.device_data.device.columns == 48
    assert coordinator.device_data.device.rows == 12
    assert coordinator.device_data.last_service_info.address == loaded_entry.unique_id
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_entry.entry_id not in hass.data.get(DOMAIN, {})
