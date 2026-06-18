"""CoolLED device color palettes and resolution."""

from __future__ import annotations

import logging

from ..const import COLOR_TYPE_COLORFUL, COLOR_TYPE_SINGLE, COLOR_TYPE_SEVEN

_LOGGER = logging.getLogger(__name__)

# RGBA tuples
OFF = (0, 0, 0, 255)
ON = (255, 255, 255, 255)
RED = (255, 0, 0, 255)
YELLOW = (255, 255, 0, 255)
GREEN = (0, 255, 0, 255)
CYAN = (0, 255, 255, 255)
BLUE = (0, 0, 255, 255)
PURPLE = (255, 0, 255, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)

PALETTE_SINGLE: dict[str, tuple[int, int, int, int]] = {
    "off": OFF,
    "on": ON,
    "black": OFF,
    "white": ON,
}

PALETTE_SEVEN: dict[str, tuple[int, int, int, int]] = {
    "off": OFF,
    "on": ON,
    "black": BLACK,
    "white": WHITE,
    "red": RED,
    "yellow": YELLOW,
    "green": GREEN,
    "cyan": CYAN,
    "blue": BLUE,
    "purple": PURPLE,
    "magenta": PURPLE,
}

PALETTE_COLORFUL: dict[str, tuple[int, int, int, int]] = {
    **PALETTE_SEVEN,
    "orange": (255, 128, 0, 255),
    "pink": (255, 105, 180, 255),
    "lime": (128, 255, 0, 255),
}

_PALETTES = {
    COLOR_TYPE_SINGLE: PALETTE_SINGLE,
    COLOR_TYPE_SEVEN: PALETTE_SEVEN,
    COLOR_TYPE_COLORFUL: PALETTE_COLORFUL,
    3: PALETTE_COLORFUL,
    4: PALETTE_COLORFUL,
}


def get_palette(color_type: int) -> dict[str, tuple[int, int, int, int]]:
    """Return the named-color palette for a device color type."""
    return _PALETTES.get(color_type, PALETTE_COLORFUL)


def palette_color_names(color_type: int) -> list[str]:
    """Color names available in payload for the given device type."""
    palette = get_palette(color_type)
    return sorted({name for name in palette if len(name) > 2})


def default_background(_color_type: int) -> tuple[int, int, int, int]:
    """Default canvas background for LED signs (off/black)."""
    return OFF


def _nearest_color(
    r: int, g: int, b: int, palette: dict[str, tuple[int, int, int, int]]
) -> tuple[int, int, int, int]:
    unique = list({v for v in palette.values()})
    best = OFF
    best_dist = float("inf")
    for color in unique:
        dist = (r - color[0]) ** 2 + (g - color[1]) ** 2 + (b - color[2]) ** 2
        if dist < best_dist:
            best_dist = dist
            best = color
    return best


def resolve_color(color: str | None, color_type: int) -> tuple[int, int, int, int] | None:
    """Map a payload color name or hex to an RGBA value for the device palette."""
    if color is None:
        return None

    palette = get_palette(color_type)
    color_str = str(color).strip().lower()

    if color_str in palette:
        return palette[color_str]

    if color_str.startswith("#"):
        try:
            h = color_str.lstrip("#")
            if len(h) >= 6:
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                return _nearest_color(r, g, b, palette)
        except ValueError:
            pass

    _LOGGER.warning(
        "Unknown color %r for color_type=%s — using off",
        color,
        color_type,
    )
    return OFF


def is_lit_pixel(r: int, g: int, b: int, color_type: int) -> bool:
    """Whether an RGB pixel should be lit when encoded to a 1-bit draw bitmap."""
    if color_type == COLOR_TYPE_SINGLE:
        return luminance(r, g, b) >= 32
    return max(r, g, b) >= 32


def luminance(r: int, g: int, b: int) -> int:
    return (r * 38 + g * 75 + b * 15) >> 7


def rgb_planes_active(
    r: int, g: int, b: int, threshold: int = 128
) -> tuple[bool, bool, bool]:
    """Return which R/G/B bitplanes are active for a pixel or text color."""
    return (r >= threshold, g >= threshold, b >= threshold)
