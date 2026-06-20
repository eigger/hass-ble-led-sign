"""BLE LED sign drivers.

This package provides a small driver abstraction so multiple BLE LED sign
families can share the same Home Assistant entities and services. The
module-level helpers below dispatch each operation to the driver selected for
a given :class:`DeviceEntry` (via ``device.driver_id``), so callers never need
to know which family they are talking to.
"""

from __future__ import annotations

from bleak.backends.device import BLEDevice
from PIL import Image

from .base import BaseLedDriver, DeviceEntry
from .data import BleLedSignBluetoothDeviceData
from .registry import DRIVERS, get_driver, match_driver

__all__ = [
    "DRIVERS",
    "BaseLedDriver",
    "BleLedSignBluetoothDeviceData",
    "DeviceEntry",
    "get_driver",
    "match_driver",
    "send_animation",
    "send_command",
    "send_image",
    "send_jt",
    "send_music",
    "send_text",
    "set_icon",
]


async def send_command(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    command: str,
    value: int | str | None = None,
) -> bool:
    return await get_driver(device.driver_id).send_command(
        ble_device, device, password, write_delay_ms, command, value
    )


async def send_text(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    text: str,
    text_color: tuple[int, int, int] = (255, 255, 255),
    **options,
) -> bool:
    return await get_driver(device.driver_id).send_text(
        ble_device,
        device,
        password,
        write_delay_ms,
        text,
        text_color=text_color,
        **options,
    )


async def send_image(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    image: Image.Image,
    threshold: int = 128,
    invert: bool = False,
    **options,
) -> bool:
    return await get_driver(device.driver_id).send_image(
        ble_device,
        device,
        password,
        write_delay_ms,
        image,
        threshold=threshold,
        invert=invert,
        **options,
    )


async def send_animation(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    image_path: str,
    speed_ms: int | None = None,
    threshold: int = 128,
    invert: bool = False,
    **options,
) -> bool:
    return await get_driver(device.driver_id).send_animation(
        ble_device,
        device,
        password,
        write_delay_ms,
        image_path,
        speed_ms=speed_ms,
        threshold=threshold,
        invert=invert,
        **options,
    )


async def send_jt(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    jt_path: str,
) -> bool:
    return await get_driver(device.driver_id).send_jt(
        ble_device, device, password, write_delay_ms, jt_path
    )


async def send_music(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    heights: list[int],
    colors: list[int],
) -> bool:
    return await get_driver(device.driver_id).send_music(
        ble_device, device, password, write_delay_ms, heights, colors
    )


async def set_icon(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    icon_id: int,
) -> bool:
    return await get_driver(device.driver_id).set_icon(
        ble_device, device, password, write_delay_ms, icon_id
    )
