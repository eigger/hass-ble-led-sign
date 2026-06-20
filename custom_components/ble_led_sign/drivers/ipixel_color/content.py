"""iPixel Color content preparation.

* Still images / GIFs are resized to the panel resolution and sent as the raw
  file bytes (the panel decodes PNG/GIF itself).
* Text is rendered to a 1-bit bitmap, split into fixed-width column chunks and
  encoded into the device's text payload (the panel handles scrolling and other
  animations itself via the properties header).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

# Bundled Galmuri pixel fonts (SIL OFL 1.1, see fonts/galmuri/LICENSE.txt).
_FONT_DIR = Path(__file__).resolve().parents[2] / "fonts" / "galmuri"
_FONT_SMALL = _FONT_DIR / "Galmuri11.ttf"
_FONT_LARGE = _FONT_DIR / "Galmuri14.ttf"

PIXEL_THRESHOLD = 128


# --------------------------------------------------------------------------- #
# Image / GIF
# --------------------------------------------------------------------------- #
def _crop_resize(img: Image.Image, width: int, height: int) -> Image.Image:
    """Resize preserving aspect ratio, centre-cropping the overflow."""
    img_aspect = img.width / img.height
    target_aspect = width / height
    if img_aspect > target_aspect:
        new_h = height
        new_w = max(1, round(height * img_aspect))
    else:
        new_w = width
        new_h = max(1, round(width / img_aspect))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def resize_image_bytes(
    file_bytes: bytes, is_gif: bool, width: int, height: int
) -> bytes:
    """Resize a still image / GIF file to the panel resolution, return file bytes."""
    img = Image.open(BytesIO(file_bytes))
    out = BytesIO()

    if is_gif:
        frames: list[Image.Image] = []
        durations: list[int] = []
        for frame in ImageSequence.Iterator(img):
            rgb = frame.convert("RGB")
            if rgb.size != (width, height):
                rgb = _crop_resize(rgb, width, height)
            frames.append(rgb.convert("P", palette=Image.ADAPTIVE, colors=256))
            durations.append(
                int(frame.info.get("duration", img.info.get("duration", 100)))
            )
        frames[0].save(
            out,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=durations if len(durations) > 1 else durations[0],
            loop=img.info.get("loop", 0),
            disposal=2,
            optimize=False,
        )
        return out.getvalue()

    rgb = img.convert("RGB")
    if rgb.size != (width, height):
        rgb = _crop_resize(rgb, width, height)
    rgb.save(out, format="PNG")
    return out.getvalue()


# --------------------------------------------------------------------------- #
# Text
# --------------------------------------------------------------------------- #
def char_height_for(panel_height: int) -> int:
    """The device supports 16px and 32px text rows."""
    return 16 if panel_height <= 20 else 32


def _render_text_row(text: str, char_height: int, font_path: str | None) -> Image.Image:
    """Render text and scale the inked area to exactly ``char_height`` rows.

    Scaling the glyphs to fill the full row height is what keeps Hangul legible
    (a syllable needs the whole 16/32-pixel column, not a partial height).
    """
    path = font_path or str(_FONT_SMALL if char_height <= 16 else _FONT_LARGE)
    font = ImageFont.truetype(path, char_height * 3)  # oversample for quality

    measure = ImageDraw.Draw(Image.new("L", (4, 4)))
    left, top, right, bottom = measure.textbbox((0, 0), text, font=font)
    width = max(1, right - left)
    height = max(1, bottom - top)
    big = Image.new("L", (width, height), 0)
    ImageDraw.Draw(big).text((-left, -top), text, fill=255, font=font)

    ink = big.getbbox()
    if ink:
        big = big.crop(ink)
    if big.height == 0 or big.width == 0:
        return Image.new("L", (1, char_height), 0)

    new_w = max(1, round(big.width * char_height / big.height))
    row = big.resize((new_w, char_height), Image.Resampling.LANCZOS)
    return row.point(lambda p: 255 if p > PIXEL_THRESHOLD else 0, mode="L")


def _encode_chunk_img(img: Image.Image) -> bytes:
    """Pack a 1-bit chunk image into rows of big-endian bits (MSB = leftmost)."""
    img = img.convert("L")
    width, height = img.size
    data = bytearray()
    for y in range(height):
        lo = 0
        hi = 0
        for x in range(width):
            if img.getpixel((x, y)):
                if x < 16:
                    lo |= 1 << (15 - x)
                else:
                    hi |= 1 << (31 - x)
        value = (hi | (lo << 16)) if width > 16 else lo
        if width <= 8:
            value >>= 8
            byte_len = 1
        elif width <= 16:
            byte_len = 2
        elif width <= 24:
            value >>= 8
            byte_len = 3
        else:
            byte_len = 4
        data += value.to_bytes(byte_len, "big")
    return bytes(data)


def _reverse_bits(data: bytes) -> bytes:
    """Reverse the bit order within each byte."""
    out = bytearray(len(data))
    for i, byte in enumerate(data):
        r = 0
        for b in range(8):
            if byte & (1 << b):
                r |= 1 << (7 - b)
        out[i] = r
    return bytes(out)


def encode_text_payload(
    text: str,
    char_height: int,
    color: tuple[int, int, int],
    *,
    animation: int = 0,
    speed: int = 80,
    rainbow: int = 0,
    bg_color: tuple[int, int, int] | None = None,
    font_path: str | None = None,
) -> bytes:
    """Build the text data payload (``[count] + properties + char blocks``).

    Scrolling and other effects are applied by the device through the
    ``animation`` byte; the client only ships the glyph bitmaps.
    """
    chunk_width = 8 if char_height <= 20 else 16
    block_type = 0x02 if char_height == 32 else 0x00
    color_bytes = bytes(color)

    img = _render_text_row(text, char_height, font_path)

    blocks = bytearray()
    count = 0
    for x0 in range(0, img.width, chunk_width):
        chunk = img.crop((x0, 0, x0 + chunk_width, char_height))
        if chunk.width < chunk_width:
            padded = Image.new("L", (chunk_width, char_height), 0)
            padded.paste(chunk, (0, 0))
            chunk = padded
        chunk_bytes = _reverse_bits(_encode_chunk_img(chunk))
        blocks += bytes([block_type]) + color_bytes + chunk_bytes
        count += 1
        if count >= 255:
            break

    properties = bytes([0x00, 0x01, 0x01, animation & 0xFF, speed & 0xFF, rainbow & 0xFF])
    properties += color_bytes
    if bg_color is not None:
        properties += bytes([0x01]) + bytes(bg_color)
    else:
        properties += bytes([0x00, 0x00, 0x00, 0x00])

    return bytes([count & 0xFF]) + properties + bytes(blocks)
