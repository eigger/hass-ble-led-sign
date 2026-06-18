"""Parse CoolLED BLE advertisement data."""

from __future__ import annotations

import logging

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from ..const import DEVICE_NAME_PREFIXES, PASSWORD_DEVICE_PREFIXES, UUID_SERVICE
from .devices import DeviceEntry

_LOGGER = logging.getLogger(__name__)


def _name_supported(name: str | None) -> bool:
    if not name:
        return False
    return any(name.startswith(prefix) for prefix in DEVICE_NAME_PREFIXES)


def _requires_password(name: str | None) -> bool:
    if not name:
        return False
    if name == "CoolLEDX":
        return True
    return any(name.startswith(prefix) for prefix in PASSWORD_DEVICE_PREFIXES)


def _use_large_mtu(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith(
        ("CoolLEDM", "CoolLEDU", "CoolLEDUX", "iLedBike", "iDevilEyes")
    )


def parse_scan_record(raw: bytes | None, name: str | None) -> DeviceEntry | None:
    """Parse device dimensions from BLE scan record."""
    entry = DeviceEntry(
        name=name or "CoolLED",
        requires_password=_requires_password(name),
        use_large_mtu=_use_large_mtu(name),
    )
    if not raw or len(raw) < 22:
        return entry

    try:
        entry.device_id = f"{raw[10]:02X}{raw[9]:02X}"
        entry.rows = raw[17] & 0xFF
        entry.columns = ((raw[18] & 0xFF) << 8) | (raw[19] & 0xFF)
        entry.color_type = raw[20] & 0xFF
        entry.version = raw[21] & 0xFF
    except IndexError:
        _LOGGER.debug("Scan record too short for full parse: %s", raw.hex())

    if entry.rows <= 0 or entry.columns <= 0:
        entry.rows = 12
        entry.columns = 48

    return entry


class CoolledBluetoothDeviceData:
    """Device data holder updated from BLE advertisements."""

    def __init__(self) -> None:
        self.device: DeviceEntry | None = None
        self.title: str | None = None
        self.last_rssi: int | None = None
        self.last_service_info: BluetoothServiceInfoBleak | None = None

    def supported(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Return True if this advertisement belongs to a CoolLED device."""
        name = service_info.name
        if _name_supported(name):
            return True
        service_uuids = {uuid.lower() for uuid in service_info.service_uuids}
        return UUID_SERVICE in service_uuids

    def update(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Update device metadata from the latest advertisement."""
        self.last_service_info = service_info
        self.last_rssi = service_info.rssi
        raw = getattr(service_info, "raw", None)
        self.device = parse_scan_record(raw, service_info.name)
        identifier = service_info.address.replace(":", "")[-8:].upper()
        model = self.device.model if self.device else "CoolLED"
        self.title = f"{identifier} ({model})"

    def get_device_name(self) -> str:
        if self.title:
            return self.title
        if self.device:
            return self.device.name
        return "CoolLED"
