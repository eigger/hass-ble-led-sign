"""Build CoolLED text/image transfer packets."""

from __future__ import annotations

import json
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from ..const import (
    CMD_ANIMATE,
    CMD_DRAW,
    CMD_TEXT,
    COLOR_TYPE_SINGLE,
    MAX_ANIMATION_FRAMES,
    TEXT_CHUNK_SIZE,
)
from .colors import luminance, resolve_color, rgb_planes_active
from .protocol import build_frame, xor_checksum


def _encode_column_plane(
    pixels,
    columns: int,
    rows: int,
    channel: int | None,
    threshold: int,
    invert: bool,
) -> list[int]:
    """Pack one graffiti bitplane (column-major, 8+4 row layout for 12px height)."""
    result: list[int] = []
    for col in range(columns):
        upper = 0
        lower = 0
        for row in range(min(8, rows)):
            r, g, b = pixels[col, row]
            lit = _pixel_lit(r, g, b, channel, threshold, invert)
            if lit:
                upper |= 1 << (7 - row)
        for row in range(8, min(12, rows)):
            r, g, b = pixels[col, row]
            lit = _pixel_lit(r, g, b, channel, threshold, invert)
            if lit:
                lower |= 1 << (11 - row)
        result.extend([upper, lower & 0x0F])
    return result


def _pixel_lit(
    r: int,
    g: int,
    b: int,
    channel: int | None,
    threshold: int,
    invert: bool,
) -> bool:
    if channel is None:
        lit = luminance(r, g, b) >= threshold
        return not lit if invert else lit
    return (r, g, b)[channel] >= threshold


def _glyph_column_bytes(pixels, width: int, height: int) -> list[int]:
    """Encode a 1-bit character glyph into column-major bytes."""
    row_bytes: list[int] = []
    for col in range(width):
        upper = 0
        lower = 0
        for row in range(min(8, height)):
            if pixels[row * width + col]:
                upper |= 1 << (7 - row)
        for row in range(8, min(12, height)):
            if pixels[row * width + col]:
                lower |= 1 << (11 - row)
        row_bytes.extend([upper, lower & 0x0F])
    return row_bytes


def build_chunked_frames(command: int, payload_body: list[int]) -> list[bytes]:
    """Split a payload into checksummed BLE frames for text/draw/animation."""
    chunks: list[list[int]] = []
    for offset in range(0, len(payload_body), TEXT_CHUNK_SIZE):
        chunks.append(payload_body[offset : offset + TEXT_CHUNK_SIZE])

    total_len = len(payload_body)
    frames: list[bytes] = []
    for index, chunk in enumerate(chunks):
        header: list[int] = [0x00]
        header.extend([(total_len >> 8) & 0xFF, total_len & 0xFF])
        header.extend([(index >> 8) & 0xFF, index & 0xFF])
        header.append(len(chunk) & 0xFF)
        packet = header + chunk
        packet.append(xor_checksum(packet))
        frames.append(build_frame([command, *packet]))
    return frames


def _render_text_bitmap(
    text: str,
    height: int,
    color_type: int = COLOR_TYPE_SINGLE,
    text_color: tuple[int, int, int] = (255, 255, 255),
) -> tuple[list[int], list[int]]:
    """Render text into per-character widths and dot-matrix bytes."""
    if not text:
        text = " "

    font_size = max(8, height - 2)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    dummy = Image.new("1", (1, 1))
    draw = ImageDraw.Draw(dummy)
    char_widths: list[int] = []
    chunks: list[bytes] = []
    planes = (
        rgb_planes_active(*text_color)
        if color_type != COLOR_TYPE_SINGLE
        else (True, False, False)
    )

    for char in text:
        bbox = draw.textbbox((0, 0), char, font=font)
        width = max(1, bbox[2] - bbox[0])
        img = Image.new("1", (width, height), 0)
        ImageDraw.Draw(img).text((0, 0), char, font=font, fill=1)
        glyph_bytes = _glyph_column_bytes(list(img.getdata()), width, height)
        char_widths.append(len(glyph_bytes))

        if color_type == COLOR_TYPE_SINGLE:
            chunks.append(bytes(glyph_bytes))
            continue

        zero_plane = bytes([0, 0] * (len(glyph_bytes) // 2))
        for plane_on in planes:
            chunks.append(bytes(glyph_bytes if plane_on else zero_plane))

    matrix = b"".join(chunks)
    return char_widths, list(matrix)


def build_text_frames(
    text: str,
    rows: int = 12,
    color_type: int = COLOR_TYPE_SINGLE,
    text_color: tuple[int, int, int] = (255, 255, 255),
) -> list[bytes]:
    """Build framed text packets for CoolLED 1248 protocol."""
    char_widths, matrix = _render_text_bitmap(
        text, rows, color_type=color_type, text_color=text_color
    )
    while len(char_widths) < 80:
        char_widths.append(0)

    payload_body: list[int] = [0x00] * 24
    payload_body.append(len(text) & 0xFF)
    payload_body.extend(char_widths[:80])
    data_len = len(matrix)
    payload_body.extend([(data_len >> 8) & 0xFF, data_len & 0xFF])
    payload_body.extend(matrix)
    return build_chunked_frames(CMD_TEXT, payload_body)


def build_draw_frames(bitmap: list[int]) -> list[bytes]:
    """Build framed draw/graffiti packets (0x03)."""
    data_len = len(bitmap)
    payload_body: list[int] = [0x00] * 24
    payload_body.extend([(data_len >> 8) & 0xFF, data_len & 0xFF])
    payload_body.extend(bitmap)
    return build_chunked_frames(CMD_DRAW, payload_body)


def build_animation_frames(
    frame_data: list[int], frame_count: int, speed_ms: int
) -> list[bytes]:
    """Build framed animation packets (0x04)."""
    payload_body: list[int] = [0x00] * 24
    payload_body.append(frame_count & 0xFF)
    payload_body.extend([(speed_ms >> 8) & 0xFF, speed_ms & 0xFF])
    payload_body.extend(frame_data)
    return build_chunked_frames(CMD_ANIMATE, payload_body)


def image_to_draw_bytes(
    image: Image.Image,
    columns: int,
    rows: int,
    threshold: int = 128,
    invert: bool = False,
    color_type: int = 0,
) -> list[int]:
    """Convert a PIL image to CoolLED graffiti/draw bytes."""
    img = image.convert("RGB").resize((columns, rows), Image.LANCZOS)
    pixels = img.load()

    if color_type == COLOR_TYPE_SINGLE:
        return _encode_column_plane(pixels, columns, rows, None, threshold, invert)

    red = _encode_column_plane(pixels, columns, rows, 0, threshold, False)
    green = _encode_column_plane(pixels, columns, rows, 1, threshold, False)
    blue = _encode_column_plane(pixels, columns, rows, 2, threshold, False)
    return red + green + blue


def images_to_animation_bytes(
    images: list[Image.Image],
    columns: int,
    rows: int,
    threshold: int = 128,
    invert: bool = False,
    color_type: int = 0,
) -> list[int]:
    """Encode each animation frame and concatenate."""
    result: list[int] = []
    for image in images:
        result.extend(
            image_to_draw_bytes(
                image,
                columns,
                rows,
                threshold=threshold,
                invert=invert,
                color_type=color_type,
            )
        )
    return result


def load_animated_images(path: str, columns: int, rows: int) -> tuple[list[Image.Image], int]:
    """Load GIF/APNG frames resized to the device resolution."""
    anim = Image.open(path)
    frame_count = getattr(anim, "n_frames", 1)
    if frame_count < 2:
        raise ValueError("Image is not animated")

    if frame_count > MAX_ANIMATION_FRAMES:
        raise ValueError(f"Animation has more than {MAX_ANIMATION_FRAMES} frames")

    frames: list[Image.Image] = []
    durations: list[int] = []
    for index in range(frame_count):
        anim.seek(index)
        frames.append(anim.convert("RGB").resize((columns, rows), Image.LANCZOS))
        durations.append(int(anim.info.get("duration", 500) or 500))

    speed_ms = max(50, min(2000, int(sum(durations) / len(durations))))
    return frames, speed_ms


def parse_jt_file(path: str) -> tuple[int, list[int], int, int]:
    """Parse a JT program file.

    Returns (command_byte, payload_body, frame_count, speed_ms).
    """
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)

    entry = document[0] if isinstance(document, list) else document
    data = entry.get("data", entry)

    payload_body: list[int] = [0x00] * 24

    if "graffitiData" in data:
        pixel_bits = [int(value) & 0xFF for value in data["graffitiData"]]
        payload_body.extend([(len(pixel_bits) >> 8) & 0xFF, len(pixel_bits) & 0xFF])
        payload_body.extend(pixel_bits)
        return CMD_DRAW, payload_body, 1, 0

    if "aniData" in data:
        pixel_bits = [int(value) & 0xFF for value in data["aniData"]]
        frame_count = int(data.get("frameNum", 1))
        delays = data.get("delays", 500)
        if isinstance(delays, list):
            speed_ms = int(delays[0]) if delays else 500
        else:
            speed_ms = int(delays)
        payload_body.append(frame_count & 0xFF)
        payload_body.extend([(speed_ms >> 8) & 0xFF, speed_ms & 0xFF])
        payload_body.extend(pixel_bits)
        return CMD_ANIMATE, payload_body, frame_count, speed_ms

    raise ValueError("JT file must contain graffitiData or aniData")


def resolve_text_color(
    color: str | None, color_type: int
) -> tuple[int, int, int]:
    """Map a service color name to an RGB tuple for text rendering."""
    if not color:
        return (255, 255, 255)
    rgba = resolve_color(color, color_type)
    if rgba is None:
        return (255, 255, 255)
    return rgba[0], rgba[1], rgba[2]


def image_file_to_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
