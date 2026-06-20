"""CoolLED BLE protocol encoding and decoding."""

from __future__ import annotations


def encode_payload(data: bytes) -> bytes:
    """Apply byte stuffing for SOF/EOF/control bytes in payload."""
    result = bytearray()
    for b in data:
        if 0x01 <= b <= 0x03:
            result.append(0x02)
            result.append(b ^ 0x04)
        else:
            result.append(b)
    return bytes(result)


def decode_payload(data: bytes) -> bytes:
    """Reverse byte stuffing."""
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == 0x02 and i + 1 < len(data):
            result.append(data[i + 1] ^ 0x04)
            i += 2
        else:
            result.append(data[i])
            i += 1
    return bytes(result)


def build_frame(command_data: list[int] | bytes) -> bytes:
    """Build a complete CoolLED BLE frame."""
    if isinstance(command_data, bytes):
        payload = command_data
    else:
        payload = bytes(command_data)

    length = len(payload)
    raw = bytes([(length >> 8) & 0xFF, length & 0xFF]) + payload
    frame = bytearray([0x01])
    frame.extend(encode_payload(raw))
    frame.append(0x03)
    return bytes(frame)


def extract_frames(data: bytes) -> list[bytes]:
    """Extract complete frames from notification data."""
    frames: list[bytes] = []
    i = 0
    while i < len(data):
        if data[i] != 0x01:
            i += 1
            continue
        j = i + 1
        while j < len(data) and data[j] != 0x03:
            j += 1
        if j < len(data):
            frames.append(data[i : j + 1])
            i = j + 1
        else:
            break
    return frames


def parse_response(data: bytes) -> list[int]:
    """Decode notification payload into command bytes."""
    results: list[int] = []
    for frame in extract_frames(data):
        inner = decode_payload(frame[1:-1])
        if len(inner) >= 2:
            results.extend(inner[2:])
    return results


def xor_checksum(data: list[int]) -> int:
    """XOR checksum used in text/draw packets."""
    value = 0
    for b in data:
        value ^= b & 0xFF
    return value & 0xFF
