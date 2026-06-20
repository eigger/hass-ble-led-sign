"""Driver for CoolLED / JTKJ family BLE LED signs."""

from __future__ import annotations

from bleak.backends.device import BLEDevice
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from PIL import Image

from ...const import MANUFACTURER, MODES_1248
from ..base import BaseLedDriver, DeviceEntry
from . import writer
from .parser import is_supported, parse_scan_record


class CoolledDriver(BaseLedDriver):
    """CoolLED 1248 / CoolLEDX / iLed* protocol driver."""

    driver_id = "coolled"
    name = "CoolLED"
    manufacturer = MANUFACTURER
    modes = MODES_1248

    @classmethod
    def match(cls, service_info: BluetoothServiceInfoBleak) -> bool:
        return is_supported(service_info)

    @classmethod
    def parse(cls, service_info: BluetoothServiceInfoBleak) -> DeviceEntry:
        return parse_scan_record(service_info)

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
            ble_device, device, password, write_delay_ms, command, value
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
            ble_device, device, password, write_delay_ms, text, text_color=text_color
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
            password,
            write_delay_ms,
            image,
            threshold=threshold,
            invert=invert,
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
            password,
            write_delay_ms,
            image_path,
            speed_ms=speed_ms,
            threshold=threshold,
            invert=invert,
        )

    async def send_jt(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        jt_path: str,
    ) -> bool:
        return await writer.send_jt(
            ble_device, device, password, write_delay_ms, jt_path
        )

    async def send_music(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        heights: list[int],
        colors: list[int],
    ) -> bool:
        return await writer.send_music(
            ble_device, device, password, write_delay_ms, heights, colors
        )

    async def set_icon(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        icon_id: int,
    ) -> bool:
        return await writer.set_icon(
            ble_device, device, password, write_delay_ms, icon_id
        )
