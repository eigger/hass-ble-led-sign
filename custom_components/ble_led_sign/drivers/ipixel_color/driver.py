"""Driver for the iPixel Color family (services 0x00FA / 0xAE00).

These signs advertise as ``LED_BLE_*``. Short control commands are
length-prefixed frames; image / GIF / text use a windowed content transfer —
the device decodes a standard PNG/GIF, so content is sent as the (resized) file
bytes.
"""

from __future__ import annotations

from bleak.backends.device import BLEDevice
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from PIL import Image

from ..base import BaseLedDriver, DeviceEntry
from . import writer
from .const import MANUFACTURER
from .parser import is_supported, parse_scan_record


class IpixelColorDriver(BaseLedDriver):
    """iPixel Color protocol driver."""

    driver_id = "ipixel_color"
    name = "iPixel Color"
    manufacturer = MANUFACTURER
    modes = {}

    # Implemented control commands.
    supports_power = True
    supports_brightness = True
    supports_speed = True  # mapped to the device's text-speed command
    supports_flip = True
    supports_clear = True
    # Extra parameterised commands reachable via the send_command service.
    extra_commands = (
        "diy_mode",
        "exit",
        "clock",
        "week",
        "sport",
        "countdown",
        "chronograph",
        "scoreboard",
        "rhythm",
        "eq",
        "password_set",
        "password_verify",
        "set_time",
        "show_slot",
        "delete_slot",
    )
    # Bulk content transfer (device decodes PNG/GIF itself).
    supports_text = True
    supports_image = True
    supports_animation = True
    # Not applicable to this family.
    supports_mode = False
    supports_icon = False
    supports_music = False
    supports_jt = False

    # Panel size/colour come from a device-info query, not the advertisement.
    requires_active_info = True

    @classmethod
    def match(cls, service_info: BluetoothServiceInfoBleak) -> bool:
        return is_supported(service_info)

    @classmethod
    def parse(cls, service_info: BluetoothServiceInfoBleak) -> DeviceEntry:
        return parse_scan_record(service_info)

    async def async_fetch_info(
        self, ble_device: BLEDevice, device: DeviceEntry, write_delay_ms: int = 0
    ) -> bool:
        return await writer.fetch_device_info(ble_device, device, write_delay_ms)

    async def send_command(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        command: str,
        value: int | str | None = None,
    ) -> bool:
        return await writer.send_command(
            ble_device, device, write_delay_ms, command, value
        )

    async def send_text(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        text: str,
        text_color: tuple[int, int, int] = (255, 255, 255),
        **options,
    ) -> bool:
        return await writer.send_text(
            ble_device,
            device,
            write_delay_ms,
            text,
            text_color=text_color,
            animation=int(options.get("animation", 0)),
            speed=int(options.get("speed", 80)),
            rainbow=int(options.get("rainbow", 0)),
            bg_color=options.get("bg_color"),
            font_path=options.get("font_path"),
            save_slot=int(options.get("save_slot", 0)),
        )

    async def send_image(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        image: Image.Image,
        threshold: int = 128,
        invert: bool = False,
        **options,
    ) -> bool:
        return await writer.send_image(
            ble_device,
            device,
            write_delay_ms,
            image,
            save_slot=int(options.get("save_slot", 0)),
        )

    async def send_animation(
        self,
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
        return await writer.send_animation(
            ble_device,
            device,
            write_delay_ms,
            image_path,
            save_slot=int(options.get("save_slot", 0)),
        )
