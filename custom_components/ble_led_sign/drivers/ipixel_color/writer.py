"""iPixel Color BLE write operations.

Short control commands are length-prefixed frames written to 0xFA02. Bulk
content (image / GIF / text-as-image) is streamed in 12 KB windows, each split
into 244-byte BLE writes and acknowledged via 0xFA03 notifications.
"""

from __future__ import annotations

import logging
from asyncio import Event, sleep, wait_for
from collections.abc import Sequence
from io import BytesIO
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from PIL import Image

from ...const import COLOR_TYPE_COLORFUL
from ..base import DeviceEntry
from .commands import (
    cmd_brightness,
    cmd_chronograph,
    cmd_clock,
    cmd_countdown,
    cmd_delete_all,
    cmd_delete_slot,
    cmd_diy_mode,
    cmd_exit,
    cmd_flip,
    cmd_password_set,
    cmd_password_verify,
    cmd_power,
    cmd_rhythm,
    cmd_rhythm_chart,
    cmd_scoreboard,
    cmd_set_time,
    cmd_show_slot,
    cmd_sport,
    cmd_text_speed,
    cmd_week,
)
from .const import MTU_SIZE, UUID_FA_NOTIFY, UUID_FA_WRITE
from .content import char_height_for, encode_text_payload, resize_image_bytes
from .parser import DEFAULT_SIZE, build_get_device_info_command, parse_device_info
from .protocol import build_content_windows, build_text_windows

_LOGGER = logging.getLogger(__name__)

CHUNK_SIZE = 244
ACK_TIMEOUT_S = 8.0


def _as_int(value: int | str | None, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _as_list(value: Any) -> list:
    if isinstance(value, (list, tuple)):
        return list(value)
    if value is None:
        return []
    return [value]


def build_command(command: str, value: int | str | Sequence | None = None) -> bytes:
    """Build the control frame for a high-level command name."""
    if command == "turn_on":
        return cmd_power(True)
    if command == "turn_off":
        return cmd_power(False)
    if command == "brightness":
        return cmd_brightness(_as_int(value))
    if command in ("speed", "text_speed"):
        return cmd_text_speed(_as_int(value))
    if command == "diy_mode":
        return cmd_diy_mode(_as_int(value))
    if command == "flip":
        return cmd_flip(bool(_as_int(value)))
    if command in ("clear", "delete_all"):
        return cmd_delete_all()
    if command == "exit":
        return cmd_exit()
    if command == "week":
        return cmd_week(_as_int(value) if value is not None else None)
    if command == "chronograph":
        return cmd_chronograph(_as_int(value))
    if command == "clock":
        v = _as_list(value)
        return cmd_clock(
            int(v[0]) if v else 0,
            bool(v[1]) if len(v) > 1 else True,
            bool(v[2]) if len(v) > 2 else False,
        )
    if command == "sport":
        v = _as_list(value)
        return cmd_sport(int(v[0]), int(v[1]), int(v[2]))
    if command == "countdown":
        v = _as_list(value)
        return cmd_countdown(int(v[0]), int(v[1]), int(v[2]))
    if command == "scoreboard":
        v = _as_list(value)
        return cmd_scoreboard(int(v[0]), int(v[1]))
    if command == "rhythm":
        v = _as_list(value)
        return cmd_rhythm(int(v[0]), int(v[1]))
    if command in ("eq", "rhythm_chart"):
        v = _as_list(value)
        return cmd_rhythm_chart(int(v[0]), [int(x) for x in v[1:]])
    if command == "password_set":
        v = _as_list(value)
        return cmd_password_set(int(v[0]), str(v[1]))
    if command == "password_verify":
        return cmd_password_verify(str(value))
    if command == "set_time":
        v = _as_list(value)
        if len(v) >= 3:
            return cmd_set_time(int(v[0]), int(v[1]), int(v[2]))
        return cmd_set_time()
    if command == "show_slot":
        return cmd_show_slot(_as_int(value))
    if command == "delete_slot":
        return cmd_delete_slot(_as_int(value))
    raise ValueError(f"Unsupported iPixel Color command: {command}")


class IpixelColorClient:
    """Low-level iPixel Color client (service 0x00FA)."""

    def __init__(
        self,
        client: BleakClient,
        device: DeviceEntry,
        write_delay_ms: int = 0,
    ) -> None:
        self.client = client
        self.device = device
        self.write_delay_ms = write_delay_ms
        self._ack_event = Event()
        self._info_event = Event()
        self._info: bytes | None = None

    def _notification_handler(self, _sender: Any, data: bytearray) -> None:
        frame = bytes(data)
        _LOGGER.debug("iPixel Color notification: %s", frame.hex())
        if len(frame) == 5 and frame[0] == 0x05:
            # Window/final ACK (data[4] in {0,1} per window, 3 = all done).
            if frame[4] in (0, 1, 3):
                self._ack_event.set()
            return
        # Any longer frame is treated as a query response (e.g. device info).
        self._info = frame
        self._info_event.set()

    async def setup(self) -> None:
        try:
            await self.client.start_notify(UUID_FA_NOTIFY, self._notification_handler)
            await sleep(0.2)
        except Exception as err:  # noqa: BLE001 - best effort
            _LOGGER.debug("iPixel Color start_notify failed: %s", err)
        try:
            await self.client.request_mtu(MTU_SIZE)
        except Exception as err:  # noqa: BLE001 - optional
            _LOGGER.debug("iPixel Color MTU request failed: %s", err)

    async def stop_notify(self) -> None:
        try:
            await self.client.stop_notify(UUID_FA_NOTIFY)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("iPixel Color stop_notify failed: %s", err)

    async def _raw_write(self, data: bytes) -> None:
        await self.client.write_gatt_char(UUID_FA_WRITE, data, response=True)
        if self.write_delay_ms > 0:
            await sleep(self.write_delay_ms / 1000.0)

    async def write_frame(self, data: bytes) -> None:
        """Write a single short control frame."""
        await self._raw_write(data)

    async def query_dimensions(self) -> tuple[int, int]:
        """Query the panel resolution, falling back to a sane default."""
        self._info_event.clear()
        try:
            await self._raw_write(build_get_device_info_command())
            await wait_for(self._info_event.wait(), ACK_TIMEOUT_S)
            if self._info is not None:
                width, height, _, _ = parse_device_info(self._info)
                _LOGGER.debug("iPixel Color panel size: %sx%s", width, height)
                return width, height
        except (TimeoutError, ValueError, IndexError) as err:
            _LOGGER.warning(
                "iPixel Color device-info query failed (%s); using %sx%s",
                err,
                *DEFAULT_SIZE,
            )
        return DEFAULT_SIZE

    def _chunk_size(self) -> int:
        # A GATT write payload is limited to (MTU - 3) bytes; cap at 244 to
        # match the reference app and stay safe if the MTU request failed.
        mtu = getattr(self.client, "mtu_size", 23) or 23
        return max(20, min(CHUNK_SIZE, mtu - 3))

    async def send_windows(self, windows: list[bytes]) -> None:
        """Stream content windows, waiting for an ACK after each."""
        chunk_size = self._chunk_size()
        for window in windows:
            self._ack_event.clear()
            for offset in range(0, len(window), chunk_size):
                await self._raw_write(window[offset : offset + chunk_size])
            try:
                await wait_for(self._ack_event.wait(), ACK_TIMEOUT_S)
            except TimeoutError as err:
                raise BleakError("No transfer ACK from device") from err


async def _with_client(ble_device: BLEDevice, device: DeviceEntry, action) -> bool:
    client: BleakClient | None = None
    try:
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        led = IpixelColorClient(client, device)
        await led.setup()
        await action(led)
        await led.stop_notify()
        return True
    except Exception as err:  # noqa: BLE001 - surfaced as a failed operation
        _LOGGER.error("iPixel Color operation failed: %s", err)
        return False
    finally:
        if client and client.is_connected:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001
                pass


def _apply_dimensions(device: DeviceEntry, width: int, height: int) -> None:
    """Write the queried panel size/colour back onto the shared device entry."""
    device.columns = width
    device.rows = height
    device.color_type = COLOR_TYPE_COLORFUL


async def fetch_device_info(
    ble_device: BLEDevice, device: DeviceEntry, write_delay_ms: int = 0
) -> bool:
    """Query the panel size/colour and store it on the device entry."""

    async def _action(client: IpixelColorClient) -> None:
        width, height = await client.query_dimensions()
        _apply_dimensions(device, width, height)

    return await _with_client(ble_device, device, _action)


async def send_command(
    ble_device: BLEDevice,
    device: DeviceEntry,
    write_delay_ms: int,
    command: str,
    value: int | str | Sequence | None = None,
) -> bool:
    """Run a single short control command."""
    frame = build_command(command, value)

    async def _action(client: IpixelColorClient) -> None:
        client.write_delay_ms = write_delay_ms
        await client.write_frame(frame)

    return await _with_client(ble_device, device, _action)


async def send_file(
    ble_device: BLEDevice,
    device: DeviceEntry,
    write_delay_ms: int,
    file_bytes: bytes,
    is_gif: bool,
    save_slot: int = 0,
) -> bool:
    """Resize an image/GIF to the panel and stream it."""

    async def _action(client: IpixelColorClient) -> None:
        client.write_delay_ms = write_delay_ms
        width, height = await client.query_dimensions()
        _apply_dimensions(device, width, height)
        resized = resize_image_bytes(file_bytes, is_gif, width, height)
        await client.send_windows(build_content_windows(resized, is_gif, save_slot))

    return await _with_client(ble_device, device, _action)


async def send_image(
    ble_device: BLEDevice,
    device: DeviceEntry,
    write_delay_ms: int,
    image: Image.Image,
    save_slot: int = 0,
) -> bool:
    """Send a still PIL image."""
    buf = BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    return await send_file(
        ble_device, device, write_delay_ms, buf.getvalue(), False, save_slot
    )


async def send_animation(
    ble_device: BLEDevice,
    device: DeviceEntry,
    write_delay_ms: int,
    image_path: str,
    save_slot: int = 0,
) -> bool:
    """Send an animated GIF file."""
    with open(image_path, "rb") as handle:
        file_bytes = handle.read()
    return await send_file(
        ble_device, device, write_delay_ms, file_bytes, True, save_slot
    )


async def send_text(
    ble_device: BLEDevice,
    device: DeviceEntry,
    write_delay_ms: int,
    text: str,
    text_color: tuple[int, int, int] = (255, 255, 255),
    *,
    animation: int = 0,
    speed: int = 80,
    rainbow: int = 0,
    bg_color: tuple[int, int, int] | None = None,
    font_path: str | None = None,
    save_slot: int = 0,
) -> bool:
    """Encode text into the device's native (animatable) text payload and send it."""

    async def _action(client: IpixelColorClient) -> None:
        client.write_delay_ms = write_delay_ms
        width, height = await client.query_dimensions()
        _apply_dimensions(device, width, height)
        payload = encode_text_payload(
            text,
            char_height_for(height),
            text_color,
            animation=animation,
            speed=speed,
            rainbow=rainbow,
            bg_color=bg_color,
            font_path=font_path,
        )
        await client.send_windows(build_text_windows(payload, save_slot))

    return await _with_client(ble_device, device, _action)
