"""iPixel Color discovery matching and device-info parsing."""

from __future__ import annotations

from datetime import datetime

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from ..base import DeviceEntry
from .const import DEVICE_NAME_PREFIXES, MANUFACTURER, MATCH_SERVICE_UUIDS

# Device-type byte (from the info response) -> internal LED type.
DEVICE_TYPE_MAP: dict[int, int] = {
    128: 0,
    129: 2,
    130: 4,
    131: 3,
    132: 1,
    133: 5,
    134: 6,
    135: 7,
    136: 8,
    137: 9,
    138: 10,
    139: 11,
    140: 12,
    141: 13,
    142: 14,
    143: 15,
    144: 16,
    145: 17,
    146: 18,
    147: 19,
}

# LED type -> (width, height).
LED_SIZE_MAP: dict[int, tuple[int, int]] = {
    0: (64, 64),
    1: (96, 16),
    2: (32, 32),
    3: (64, 16),
    4: (32, 16),
    5: (64, 20),
    6: (128, 32),
    7: (144, 16),
    8: (192, 16),
    9: (48, 24),
    10: (64, 32),
    11: (96, 32),
    12: (128, 32),
    13: (96, 32),
    14: (160, 32),
    15: (192, 32),
    16: (256, 32),
    17: (320, 32),
    18: (384, 32),
    19: (448, 32),
}

# Used when the device type is unknown / the query fails.
DEFAULT_SIZE: tuple[int, int] = (32, 32)


def is_supported(service_info: BluetoothServiceInfoBleak) -> bool:
    """Return True if this advertisement belongs to an iPixel Color device."""
    name = service_info.name or ""
    if any(name.startswith(prefix) for prefix in DEVICE_NAME_PREFIXES):
        return True
    service_uuids = {uuid.lower() for uuid in service_info.service_uuids}
    return bool(service_uuids & MATCH_SERVICE_UUIDS)


def parse_scan_record(service_info: BluetoothServiceInfoBleak) -> DeviceEntry:
    """Build a :class:`DeviceEntry` from an advertisement.

    The advertisement does not carry the panel resolution; it is read live from
    a device-info query when content is sent (see :func:`parse_device_info`).
    """
    return DeviceEntry(
        name=service_info.name or "iPixel Color",
        driver_id="ipixel_color",
        manufacturer=MANUFACTURER,
    )


def build_get_device_info_command() -> bytes:
    """Frame requesting device info (``08 00 01 80 hh mm ss lang``)."""
    now = datetime.now()
    return bytes([8, 0, 1, 0x80, now.hour, now.minute, now.second, 0])


def parse_device_info(response: bytes) -> tuple[int, int, int, int]:
    """Parse a device-info notify frame.

    Returns ``(width, height, device_type, password_flag)``.
    """
    if len(response) < 5:
        raise ValueError(f"Device info response too short: {response.hex()}")
    device_type = response[4]
    led_type = DEVICE_TYPE_MAP.get(device_type, 0)
    width, height = LED_SIZE_MAP.get(led_type, DEFAULT_SIZE)
    password_flag = response[10] if len(response) >= 11 else 255
    return width, height, device_type, password_flag
