"""Generate Home Assistant brand images for BLE LED Sign.

The artwork is an original geometric brand mark on a dark navy rounded square:
a cyan-bezeled LED matrix sign displaying glowing pixel-matrix characters on an
unlit LED dot grid, paired with golden wireless signal arcs at the upper right.
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
GOLD = "#f2a900"
ORANGE = "#ff8c1a"
CORAL = "#ff5c77"
GREEN = "#34d399"
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


def _draw_arc_ring(
    d: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r_in: float,
    r_out: float,
    deg_start: float,
    deg_end: float,
    fill: str,
) -> None:
    """Draw a smooth annular sector."""
    steps = 48
    a0 = math.radians(deg_start)
    a1 = math.radians(deg_end)
    pts_out = [
        (
            cx + r_out * math.cos(a0 + (a1 - a0) * i / steps),
            cy + r_out * math.sin(a0 + (a1 - a0) * i / steps),
        )
        for i in range(steps + 1)
    ]
    pts_in = [
        (
            cx + r_in * math.cos(a0 + (a1 - a0) * i / steps),
            cy + r_in * math.sin(a0 + (a1 - a0) * i / steps),
        )
        for i in range(steps + 1)
    ]
    d.polygon(pts_out + list(reversed(pts_in)), fill=fill)


def draw_icon() -> Image.Image:
    """Draw the 512px RGBA app icon."""
    s = SCALE
    image = Image.new("RGBA", (SIZE * s, SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)

    def box(x0: float, y0: float, x1: float, y1: float) -> list[float]:
        return [x0 * s, y0 * s, x1 * s, y1 * s]

    # 1. Dark navy rounded square background.
    d.rounded_rectangle(box(0, 0, SIZE - 1, SIZE - 1), radius=104 * s, fill=NAVY)

    # 2. LED Matrix Sign outer frame (cyan) and dark matrix recess.
    d.rounded_rectangle(box(44, 156, 432, 412), radius=36 * s, fill=CYAN)
    d.rounded_rectangle(box(66, 178, 410, 390), radius=22 * s, fill=PANEL_DARK)

    # Subtle bottom RGB status strip along the sign frame.
    d.rounded_rectangle(box(148, 428, 212, 442), radius=7 * s, fill=YELLOW)
    d.rounded_rectangle(box(224, 428, 288, 442), radius=7 * s, fill=GREEN)
    d.rounded_rectangle(box(300, 428, 364, 442), radius=7 * s, fill=CORAL)

    # 3. 11x5 LED dot matrix inside the dark panel.
    cols = 11
    rows = 5
    pitch_x = 28.0
    pitch_y = 32.0
    start_x = 238.0 - (cols - 1) * pitch_x / 2.0
    start_y = 284.0 - (rows - 1) * pitch_y / 2.0
    dot_r = 10.6

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

    # 4. Golden BLE wireless signal arcs with a clean navy knockout around the node.
    acx, acy = 356 * s, 140 * s
    d.ellipse([acx - 28 * s, acy - 28 * s, acx + 28 * s, acy + 28 * s], fill=NAVY)
    d.ellipse([acx - 16 * s, acy - 16 * s, acx + 16 * s, acy + 16 * s], fill=YELLOW)
    for r_in, r_out, col in (
        (32 * s, 48 * s, YELLOW),
        (60 * s, 76 * s, GOLD),
        (88 * s, 104 * s, ORANGE),
    ):
        _draw_arc_ring(d, acx, acy, r_in, r_out, -78, 8, fill=col)

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
