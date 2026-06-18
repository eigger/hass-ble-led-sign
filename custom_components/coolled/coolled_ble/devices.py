"""CoolLED device metadata from BLE advertisement."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(slots=True)
class DeviceEntry:
    """Parsed CoolLED device information."""

    name: str
    rows: int = 12
    columns: int = 48
    color_type: int = 0
    device_id: str = ""
    version: int = 0
    requires_password: bool = False
    use_large_mtu: bool = False

    @property
    def width(self) -> int:
        """Canvas width for label renderer (columns)."""
        return self.columns

    @property
    def height(self) -> int:
        """Canvas height for label renderer (rows)."""
        return self.rows

    @property
    def model(self) -> str:
        return f"{self.rows}x{self.columns}"

    @property
    def color_type_name(self) -> str:
        from ..const import COLOR_TYPE_NAMES

        return COLOR_TYPE_NAMES.get(self.color_type, "unknown")

    @property
    def color_type_label(self) -> str:
        from ..const import COLOR_TYPE_LABELS

        return COLOR_TYPE_LABELS.get(self.color_type, self.color_type_name)

    @property
    def is_monochrome_output(self) -> bool:
        """Draw/graffiti uses a single bitplane on single-color hardware."""
        return self.color_type == 0

    @property
    def draw_byte_count(self) -> int:
        """Bitmap size for graffiti command (1 or 3 RGB bitplanes)."""
        planes = 1 if self.color_type == 0 else 3
        return self.columns * 2 * planes
