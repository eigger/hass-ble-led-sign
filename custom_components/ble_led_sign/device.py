"""Device registry helpers for the BLE LED Sign integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo

from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER
from .drivers import BaseLedDriver, DeviceEntry
from .types import BleLedSignConfigEntry


def build_device_info(address: str) -> DeviceInfo:
    """Minimal entity device info; metadata lives in the device registry."""
    return DeviceInfo(connections={(CONNECTION_BLUETOOTH, address)})


def get_entry_driver(hass: HomeAssistant, entry_id: str) -> BaseLedDriver | None:
    """Return the resolved driver for a config entry, if known."""
    return hass.data.get(DOMAIN, {}).get(entry_id, {}).get("driver")


def driver_supports(hass: HomeAssistant, entry_id: str, capability: str) -> bool:
    """Return True if the entry's driver supports a capability.

    When the driver is unknown (no advertisement seen yet), default to True so
    entities are still created rather than silently dropped.
    """
    driver = get_entry_driver(hass, entry_id)
    if driver is None:
        return True
    return bool(getattr(driver, capability, True))


def sync_device_registry(
    hass: HomeAssistant,
    entry: BleLedSignConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Update device registry with scan-record metadata."""
    address = entry.unique_id
    assert address is not None

    device_data = entry.runtime_data.device_data
    device: DeviceEntry | None = device_data.device
    identifier = address.replace(":", "")[-8:].upper()

    manufacturer = (
        device.manufacturer if device and device.manufacturer else MANUFACTURER
    )

    kwargs: dict[str, Any] = {
        "config_entry_id": entry.entry_id,
        "connections": {(CONNECTION_BLUETOOTH, address)},
        "manufacturer": manufacturer,
        "name": service_info.name or f"{DEFAULT_NAME} {identifier}",
    }

    if device:
        kwargs["model"] = f"{device.rows}×{device.columns}"
        if device.device_id:
            kwargs["serial_number"] = device.device_id
        if device.version:
            kwargs["sw_version"] = f"0x{device.version:02X}"
        kwargs["hw_version"] = device.color_type_label

    dr.async_get(hass).async_get_or_create(**kwargs)
