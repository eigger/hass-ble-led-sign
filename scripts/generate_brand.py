"""Generate Home Assistant brand images for BLE LED Sign.

The artwork is an original geometric brand mark on a dark navy rounded square:
a centered cyan-bezeled LED matrix sign displaying glowing pixel-matrix
characters on an unlit LED dot grid, paired with a crisp Bluetooth rune symbol.
Drawn from geometric primitives at 4x scale and downsampled, so no source image,
external font file, or network access is needed. Run with Pillow 12.3.0 for
reproducible PNGs.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND = Path(__file__).resolve().parents[1] / "custom_components/ble_led_sign/brand"
SIZE = 512
SCALE = 4
NAVY = "#1b2a41"
PANEL_DARK = "#0f172a"
DOT_OFF = "#233554"
CYAN = "#38bdf8"
YELLOW = "#ffd23f"
CORAL = "#ff5c77"
WORDMARK = "#e0a100"

# 11 columns x 5 rows pixel-matrix pattern spelling "LED".
LED_BITMAP = [
    "10001110110",
    "10001000101",
    "10001110101",
    "10001000101",
    "11101110110",
]

COL_COLORS = [
    YELLOW,
    YELLOW,
    YELLOW,
    DOT_OFF,
    CYAN,
    CYAN,
    CYAN,
    DOT_OFF,
    CORAL,
    CORAL,
    CORAL,
]


def _draw_thick_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    width: float,
    color: str,
) -> None:
    """Draw a thick polyline with perfectly round caps and joins."""
    r = width / 2.0
    for x, y in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:], strict=False):
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        nx = -dy / length * r
        ny = dx / length * r
        draw.polygon(
            [
                (x1 + nx, y1 + ny),
                (x2 + nx, y2 + ny),
                (x2 - nx, y2 - ny),
                (x1 - nx, y1 - ny),
            ],
            fill=color,
        )


def _draw_bluetooth_rune(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    half_h: float,
    w_right: float,
    w_left: float,
    stroke: float,
    color: str,
    s: int,
) -> None:
    """Draw a clean geometric Bluetooth rune centered at (cx, cy)."""
    _draw_thick_polyline(
        draw,
        [(cx * s, (cy - half_h) * s), (cx * s, (cy + half_h) * s)],
        stroke * s,
        color,
    )
    _draw_thick_polyline(
        draw,
        [
            (cx * s, (cy - half_h) * s),
            ((cx + w_right) * s, (cy - half_h * 0.5) * s),
            ((cx - w_left) * s, (cy + half_h * 0.5) * s),
        ],
        stroke * s,
        color,
    )
    _draw_thick_polyline(
        draw,
        [
            (cx * s, (cy + half_h) * s),
            ((cx + w_right) * s, (cy + half_h * 0.5) * s),
            ((cx - w_left) * s, (cy - half_h * 0.5) * s),
        ],
        stroke * s,
        color,
    )


def draw_icon() -> Image.Image:
    """Draw the 512px RGBA app icon."""
    s = SCALE
    image = Image.new("RGBA", (SIZE * s, SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)

    def box(x0: float, y0: float, x1: float, y1: float) -> list[float]:
        return [x0 * s, y0 * s, x1 * s, y1 * s]

    # 1. Dark navy rounded square background.
    d.rounded_rectangle(box(0, 0, SIZE - 1, SIZE - 1), radius=104 * s, fill=NAVY)

    # 2. Crisp Bluetooth rune badge centered above the LED matrix sign.
    _draw_bluetooth_rune(
        d,
        cx=256.0,
        cy=82.0,
        half_h=38.0,
        w_right=26.0,
        w_left=24.0,
        stroke=11.0,
        color=CYAN,
        s=s,
    )

    # 3. Centered LED Matrix Sign outer frame (cyan) and dark matrix recess.
    d.rounded_rectangle(box(44, 148, 468, 424), radius=40 * s, fill=CYAN)
    d.rounded_rectangle(box(68, 172, 444, 400), radius=24 * s, fill=PANEL_DARK)

    # 4. Centered 11x5 LED dot matrix inside the dark panel.
    cols = 11
    rows = 5
    pitch_x = 30.8
    pitch_y = 35.0
    start_x = 256.0 - (cols - 1) * pitch_x / 2.0
    start_y = 286.0 - (rows - 1) * pitch_y / 2.0
    dot_r = 11.6

    for r_idx, row_str in enumerate(LED_BITMAP):
        cy = start_y + r_idx * pitch_y
        for c_idx, ch in enumerate(row_str):
            cx = start_x + c_idx * pitch_x
            if ch == "1":
                col = COL_COLORS[c_idx]
                d.ellipse(
                    box(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r),
                    fill=col,
                )
            else:
                d.ellipse(
                    box(
                        cx - dot_r * 0.78,
                        cy - dot_r * 0.78,
                        cx + dot_r * 0.78,
                        cy + dot_r * 0.78,
                    ),
                    fill=DOT_OFF,
                )

    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    """Write icon.png, icon@2x.png, logo.png and logo@2x.png."""
    BRAND.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(BRAND / "icon@2x.png", optimize=True)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(
        BRAND / "icon.png", optimize=True
    )

    # Pillow bundles Aileron Regular, so regeneration needs no system fonts.
    font = ImageFont.load_default(size=320)
    bounds = font.getbbox("LED Sign")
    wordmark = Image.new("RGBA", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
    ImageDraw.Draw(wordmark).text(
        (-bounds[0], -bounds[1]), "LED Sign", font=font, fill=WORDMARK
    )
    wordmark = wordmark.crop(wordmark.getbbox())
    gap = 96 + ((SIZE + 96 + wordmark.width) % 2)
    logo = Image.new("RGBA", (SIZE + gap + wordmark.width, SIZE))
    logo.alpha_composite(icon, (0, 0))
    logo.alpha_composite(wordmark, (SIZE + gap, (SIZE - wordmark.height) // 2))
    logo = logo.crop(logo.getbbox())
    logo.save(BRAND / "logo@2x.png", optimize=True)
    logo.resize((logo.width // 2, logo.height // 2), Image.Resampling.LANCZOS).save(
        BRAND / "logo.png", optimize=True
    )


if __name__ == "__main__":
    main()
