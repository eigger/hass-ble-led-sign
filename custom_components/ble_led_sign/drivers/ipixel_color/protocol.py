"""iPixel Color BLE wire framing.

Short control frame::

    [len_lo, len_hi, command, subcommand, *payload]

``len`` is the little-endian total frame length (including the two length
bytes); there is no checksum or byte stuffing.

Bulk content (image / GIF / text) is streamed in length-prefixed windows. The
panel decodes an embedded PNG/GIF itself, so the raw (resized) file bytes are
sent as the window payload::

    window = len(2 LE) + [type, 0x00, option] + size(4 LE) + crc32(4 LE)
             + [tail, save_slot] + chunk

``type``/``tail`` are ``0x02``/``0x00`` for a still image and ``0x03``/``0x02``
for an animated GIF; ``option`` is ``0x00`` for the first window then ``0x02``;
``size``/``crc32`` cover the whole file.
"""

from __future__ import annotations

import binascii

WINDOW_SIZE = 12 * 1024


def build_frame(command: int, subcommand: int, *payload: int) -> bytes:
    """Build a length-prefixed control frame."""
    body = [command & 0xFF, subcommand & 0xFF, *(b & 0xFF for b in payload)]
    total = 2 + len(body)
    return bytes([total & 0xFF, (total >> 8) & 0xFF, *body])


def build_windows(
    payload: bytes,
    type0: int,
    type1: int,
    tail: int,
    save_slot: int = 0,
) -> list[bytes]:
    """Split a payload into length-prefixed transfer windows.

    Each window carries the whole payload's size + CRC32 and one ≤12 KB chunk:
    ``len(2 LE) + [type0, type1, option] + size(4 LE) + crc32(4 LE)
    + [tail, save_slot] + chunk``.
    """
    size_bytes = len(payload).to_bytes(4, "little")
    crc_bytes = (binascii.crc32(payload) & 0xFFFFFFFF).to_bytes(4, "little")

    windows: list[bytes] = []
    pos = 0
    index = 0
    while pos < len(payload):
        chunk = payload[pos : pos + WINDOW_SIZE]
        option = 0x00 if index == 0 else 0x02
        frame = (
            bytes([type0 & 0xFF, type1 & 0xFF, option])
            + size_bytes
            + crc_bytes
            + bytes([tail & 0xFF, save_slot & 0xFF])
            + chunk
        )
        prefix = (2 + len(frame)).to_bytes(2, "little")
        windows.append(prefix + frame)
        index += 1
        pos += WINDOW_SIZE
    return windows


def build_content_windows(
    file_bytes: bytes, is_gif: bool, save_slot: int = 0
) -> list[bytes]:
    """Windows for a still image (``02 00``/tail ``00``) or GIF (``03 00``/tail ``02``)."""
    if is_gif:
        return build_windows(file_bytes, 0x03, 0x00, 0x02, save_slot)
    return build_windows(file_bytes, 0x02, 0x00, 0x00, save_slot)


def build_text_windows(payload: bytes, save_slot: int = 0) -> list[bytes]:
    """Windows for a text payload (``00 01``/tail ``00``)."""
    return build_windows(payload, 0x00, 0x01, 0x00, save_slot)
