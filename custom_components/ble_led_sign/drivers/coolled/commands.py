"""CoolLED BLE command builders."""

from __future__ import annotations

from .protocol import build_frame


def cmd_switch(on: bool) -> bytes:
    """Power ON/OFF."""
    return build_frame([0x09, 0x01 if on else 0x00])


def cmd_brightness(level: int) -> bytes:
    """Set brightness (CoolLED 1248 expects the value offset by 10)."""
    return build_frame([0x08, level & 0xFF])


def cmd_speed(speed: int) -> bytes:
    """Set scroll speed."""
    return build_frame([0x07, speed & 0xFF])


def cmd_mode(mode: int) -> bytes:
    """Set scroll/display mode (1-indexed on wire)."""
    return build_frame([0x06, mode & 0xFF])


def cmd_begin_transfer() -> bytes:
    """Begin text/image transfer."""
    return build_frame([0x0A])


def cmd_password_check(password: str = "000000") -> bytes:
    """Verify 6-digit ASCII password."""
    pwd = (password or "000000")[:6].ljust(6, "0")
    return build_frame([0x0D, *[ord(c) for c in pwd]])


def cmd_icon(icon_id: int) -> bytes:
    """Select built-in icon."""
    return build_frame([0x05, icon_id & 0xFF])


def cmd_music(heights: list[int], colors: list[int]) -> bytes:
    """Set music equalizer bars (8 heights + 8 color indices)."""
    h = [value & 0xFF for value in heights[:8]]
    c = [value & 0xFF for value in colors[:8]]
    while len(h) < 8:
        h.append(0)
    while len(c) < 8:
        c.append(0)
    return build_frame([0x01, *h, *c])


def cmd_draw(bitmap: list[int] | bytes) -> bytes:
    """Send graffiti/draw bitmap."""
    if isinstance(bitmap, bytes):
        data = list(bitmap)
    else:
        data = bitmap
    return build_frame([0x03, *data])
