"""CoolLED device registry helpers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo

from .const import MANUFACTURER
from .coolled_ble.devices import DeviceEntry
from .types import CoolledConfigEntry


def build_device_info(address: str) -> DeviceInfo:
    """Minimal entity device info; metadata lives in the device registry."""
    return DeviceInfo(connections={(CONNECTION_BLUETOOTH, address)})


def sync_device_registry(
    hass: HomeAssistant,
    entry: CoolledConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Update device registry with scan-record metadata."""
    address = entry.unique_id
    assert address is not None

    device_data = entry.runtime_data.device_data
    device: DeviceEntry | None = device_data.device
    identifier = address.replace(":", "")[-8:].upper()

    kwargs: dict[str, Any] = {
        "config_entry_id": entry.entry_id,
        "connections": {(CONNECTION_BLUETOOTH, address)},
        "manufacturer": MANUFACTURER,
        "name": service_info.name or f"CoolLED {identifier}",
    }

    if device:
        kwargs["model"] = f"{device.rows}×{device.columns}"
        if device.device_id:
            kwargs["serial_number"] = device.device_id
        if device.version:
            kwargs["sw_version"] = f"0x{device.version:02X}"
        kwargs["hw_version"] = device.color_type_label

    dr.async_get(hass).async_get_or_create(**kwargs)
