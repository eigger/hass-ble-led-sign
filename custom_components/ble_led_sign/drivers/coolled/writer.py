"""CoolLED BLE write operations."""

from __future__ import annotations

import logging
from asyncio import sleep

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from blesession import Notifications, SessionTrace, guarded_write
from PIL import Image

from ...ble import AuthenticationRejected, run_protocol
from ...const import (
    BRIGHTNESS_OFFSET,
    DEFAULT_SPLIT_WRITE,
    MAX_PACKET_RETRIES,
    MTU_SIZE,
    MTU_SPLIT_WRITE,
    PACKET_DELAY_MS,
    RESPONSE_TIMEOUT_S,
    UUID_CHAR,
)
from ..base import DeviceEntry
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
        trace: SessionTrace | None = None,
    ) -> None:
        self.trace = trace if trace is not None else SessionTrace()
        self.client = client
        self.device = device
        self.password = password
        self.write_delay_ms = write_delay_ms
        self.split_write = (
            MTU_SPLIT_WRITE if device.use_large_mtu else DEFAULT_SPLIT_WRITE
        )
        self._replies = Notifications(client, UUID_CHAR, settle=0.3)

    async def start_notify(self) -> None:
        await self._replies.__aenter__()

    async def stop_notify(self) -> None:
        await self._replies.__aexit__(None, None, None)

    async def _write_raw(self, data: bytes, response: bool = False) -> None:
        delay = self.write_delay_ms / 1000.0
        for offset in range(0, len(data), self.split_write):
            chunk = data[offset : offset + self.split_write]
            await guarded_write(
                self.client, UUID_CHAR, chunk, response=response, step="write"
            )
            if delay > 0:
                await sleep(delay)

    async def _write(self, data: bytes, wait_response: bool = False) -> list[int]:
        self._replies.clear()
        await self._write_raw(data)
        if not wait_response:
            return []
        frame = await self._replies.next(RESPONSE_TIMEOUT_S, step="response")
        response = parse_response(frame)
        if not response:
            raise BleakError("Malformed response from LED sign")
        return response

    async def setup(self) -> None:
        if self.device.use_large_mtu:
            try:
                await self.client.request_mtu(MTU_SIZE)
            except Exception as err:
                _LOGGER.debug("MTU request failed: %s", err)
        await self.start_notify()
        if self.device.requires_password:
            with self.trace.timed("auth"):
                response = await self._write(
                    cmd_password_check(self.password), wait_response=True
                )
                if response and response[-1] != 0x00:
                    raise AuthenticationRejected("Password verification failed")

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
                if response[-1] == 0x00:
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

    async def send_payload_transfer(
        self, command: int, payload_body: list[int]
    ) -> None:
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
    return await run_protocol(
        ble_device,
        lambda client, trace: CoolledClient(
            client, device, password, write_delay_ms, trace
        ),
        action,
    )


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
            # CoolLED 1248 expects the HA brightness (0-255) offset by 10.
            await client.set_brightness(int(value or 0) + BRIGHTNESS_OFFSET)
        elif command == "speed":
            await client.set_speed(int(value or 0))
        elif command == "mode":
            await client.set_mode(int(value or 1))
        elif command == "icon":
            await client.send_icon(int(value or 0))
        else:
            raise ValueError(f"Unknown command: {command}")

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


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

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


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

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


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

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


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

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


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

    return await _with_client(ble_device, device, password, write_delay_ms, _action)


async def set_icon(
    ble_device: BLEDevice,
    device: DeviceEntry,
    password: str,
    write_delay_ms: int,
    icon_id: int,
) -> bool:
    async def _action(client: CoolledClient) -> None:
        await client.send_icon(icon_id)

    return await _with_client(ble_device, device, password, write_delay_ms, _action)
