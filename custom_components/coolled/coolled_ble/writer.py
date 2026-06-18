"""CoolLED BLE write operations."""

from __future__ import annotations

import logging
from asyncio import Event, sleep, wait_for
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from PIL import Image

from ..const import (
    DEFAULT_SPLIT_WRITE,
    MAX_PACKET_RETRIES,
    MTU_SIZE,
    MTU_SPLIT_WRITE,
    PACKET_DELAY_MS,
    RESPONSE_TIMEOUT_S,
    UUID_CHAR,
)
from .commands import (
    cmd_begin_transfer,
    cmd_brightness,
    cmd_icon,
    cmd_mode,
    cmd_music,
    cmd_password_check,
    cmd_speed,
    cmd_switch,
)
from .devices import DeviceEntry
from .protocol import parse_response
from .text import (
    build_animation_frames,
    build_chunked_frames,
    build_draw_frames,
    build_text_frames,
    image_to_draw_bytes,
    images_to_animation_bytes,
    load_animated_images,
    parse_jt_file,
)

_LOGGER = logging.getLogger(__name__)


class BleakCharacteristicMissing(BleakError):
    """Characteristic missing on device."""


class CoolledClient:
    """Low-level CoolLED BLE client."""

    def __init__(
        self,
        client: BleakClient,
        device: DeviceEntry,
        password: str = "000000",
        write_delay_ms: int = PACKET_DELAY_MS,
    ) -> None:
        self.client = client
        self.device = device
        self.password = password
        self.write_delay_ms = write_delay_ms
        self.split_write = (
            MTU_SPLIT_WRITE if device.use_large_mtu else DEFAULT_SPLIT_WRITE
        )
        self._event = Event()
        self._last_response: list[int] = []

    async def start_notify(self) -> None:
        await self.client.start_notify(UUID_CHAR, self._notification_handler)
        await sleep(0.3)

    async def stop_notify(self) -> None:
        await self.client.stop_notify(UUID_CHAR)

    def _notification_handler(self, _sender: Any, data: bytearray) -> None:
        self._last_response = parse_response(bytes(data))
        self._event.set()
        _LOGGER.debug("Notification: %s", self._last_response)

    async def _write_raw(self, data: bytes, response: bool = False) -> None:
        delay = self.write_delay_ms / 1000.0
        for offset in range(0, len(data), self.split_write):
            chunk = data[offset : offset + self.split_write]
            await self.client.write_gatt_char(UUID_CHAR, chunk, response)
            if delay > 0:
                await sleep(delay)

    async def _write(self, data: bytes, wait_response: bool = False) -> list[int]:
        self._event.clear()
        await self._write_raw(data)
        if not wait_response:
            return []
        try:
            await wait_for(self._event.wait(), RESPONSE_TIMEOUT_S)
        except TimeoutError:
            _LOGGER.warning("Response timeout")
        return self._last_response

    async def setup(self) -> None:
        if self.device.use_large_mtu:
            try:
                await self.client.request_mtu(MTU_SIZE)
            except Exception as err:
                _LOGGER.debug("MTU request failed: %s", err)
        await self.start_notify()
        if self.device.requires_password:
            response = await self._write(
                cmd_password_check(self.password), wait_response=True
            )
            if response and response[-1] != 0x00:
                raise BleakError("Password verification failed")

    async def turn_on(self) -> None:
        await self._write(cmd_switch(True))

    async def turn_off(self) -> None:
        await self._write(cmd_switch(False))

    async def set_brightness(self, level: int) -> None:
        await self._write(cmd_brightness(level))

    async def set_speed(self, speed: int) -> None:
        await self._write(cmd_speed(speed))

    async def set_mode(self, mode: int) -> None:
        await self._write(cmd_mode(mode))

    async def send_icon(self, icon_id: int) -> None:
        await self._write(cmd_icon(icon_id))

    async def set_music_bars(self, heights: list[int], colors: list[int]) -> None:
        await self._write(cmd_music(heights, colors))

    async def _send_chunked_transfer(self, frames: list[bytes]) -> None:
        for frame in frames:
            for attempt in range(1, MAX_PACKET_RETRIES + 1):
                response = await self._write(frame, wait_response=True)
                if not response or response[-1] == 0x00:
                    break
                _LOGGER.warning(
                    "Transfer packet retry %s/%s", attempt, MAX_PACKET_RETRIES
                )
                if attempt == MAX_PACKET_RETRIES:
                    raise BleakError("Chunked transfer failed")

    async def send_draw(self, bitmap: list[int]) -> None:
        await self._write(cmd_begin_transfer())
        await self._send_chunked_transfer(build_draw_frames(bitmap))

    async def send_animation(
        self, frame_data: list[int], frame_count: int, speed_ms: int
    ) -> None:
        await self._write(cmd_begin_transfer())
        await self._send_chunked_transfer(
            build_animation_frames(frame_data, frame_count, speed_ms)
        )

    async def send_payload_transfer(self, command: int, payload_body: list[int]) -> None:
        await self._write(cmd_begin_transfer())
        await self._send_chunked_transfer(build_chunked_frames(command, payload_body))

    async def send_text(
        self,
        text: str,
        text_color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        await self._write(cmd_begin_transfer())
        frames = build_text_frames(
            text,
            self.device.rows,
            color_type=self.device.color_type,
            text_color=text_color,
        )
        await self._send_chunked_transfer(frames)


async def _with_client(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    action,
) -> bool:
    client: BleakClient | None = None
    try:
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        coolled = CoolledClient(client, device, password, write_delay_ms)
        await coolled.setup()
        await action(coolled)
        try:
            await coolled.stop_notify()
        except Exception as err:
            _LOGGER.debug("Stop notify: %s", err)
        return True
    except Exception as err:
        _LOGGER.error("CoolLED operation failed: %s", err)
        return False
    finally:
        if client and client.is_connected:
            try:
                await client.disconnect()
            except Exception:
                pass


async def send_command(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    command: str,
    value: int | str | None = None,
) -> bool:
    """Send a simple command to the device."""

    async def _action(client: CoolledClient) -> None:
        if command == "turn_on":
            await client.turn_on()
        elif command == "turn_off":
            await client.turn_off()
        elif command == "brightness":
            await client.set_brightness(int(value or 0))
        elif command == "speed":
            await client.set_speed(int(value or 0))
        elif command == "mode":
            await client.set_mode(int(value or 1))
        elif command == "icon":
            await client.send_icon(int(value or 0))
        else:
            raise ValueError(f"Unknown command: {command}")

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )


async def send_text(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    text: str,
    text_color: tuple[int, int, int] = (255, 255, 255),
) -> bool:
    async def _action(client: CoolledClient) -> None:
        await client.send_text(text, text_color=text_color)

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )


async def send_image(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    image: Image.Image,
    threshold: int = 128,
    invert: bool = False,
) -> bool:
    async def _action(client: CoolledClient) -> None:
        bitmap = image_to_draw_bytes(
            image,
            device.columns,
            device.rows,
            threshold=threshold,
            invert=invert,
            color_type=device.color_type,
        )
        await client.send_draw(bitmap)

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
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
) -> bool:
    async def _action(client: CoolledClient) -> None:
        frames, detected_speed = load_animated_images(
            image_path, device.columns, device.rows
        )
        frame_data = images_to_animation_bytes(
            frames,
            device.columns,
            device.rows,
            threshold=threshold,
            invert=invert,
            color_type=device.color_type,
        )
        await client.send_animation(
            frame_data,
            len(frames),
            speed_ms if speed_ms is not None else detected_speed,
        )

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )


async def send_jt(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    jt_path: str,
) -> bool:
    async def _action(client: CoolledClient) -> None:
        command, payload_body, _, _ = parse_jt_file(jt_path)
        await client.send_payload_transfer(command, payload_body)

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )


async def send_music(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    heights: list[int],
    colors: list[int],
) -> bool:
    async def _action(client: CoolledClient) -> None:
        await client.set_music_bars(heights, colors)

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )


async def set_icon(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    icon_id: int,
) -> bool:
    async def _action(client: CoolledClient) -> None:
        await client.send_icon(icon_id)

    return await _with_client(
        ble_device, device, password, write_delay_ms, _action
    )
