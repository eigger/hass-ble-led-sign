"""Base driver abstraction for BLE LED signs.

Each supported device family is implemented as a driver that knows how to
recognise its advertisements, parse device metadata and perform the BLE
operations exposed by the integration.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod

from bleak.backends.device import BLEDevice
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from PIL import Image


@dataclasses.dataclass(slots=True)
class DeviceEntry:
    """Parsed BLE LED sign device information."""

    name: str
    driver_id: str = "coolled"
    manufacturer: str = ""
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


class BaseLedDriver(ABC):
    """Abstract driver for a BLE LED sign family.

    Concrete drivers are stateless: every method receives the BLE device and
    parsed :class:`DeviceEntry` so a single class instance can serve every
    config entry that uses the same family.
    """

    #: Stable identifier stored on :class:`DeviceEntry.driver_id`.
    driver_id: str = ""
    #: Human readable family name (used in logs / device registry fallback).
    name: str = ""
    #: Default manufacturer reported to the device registry.
    manufacturer: str = ""
    #: Scroll/display modes exposed as light effects and the mode select.
    modes: dict[int, str] = {}

    # --- capability flags (override per driver) ---
    supports_power: bool = True
    supports_brightness: bool = True
    supports_speed: bool = True
    supports_mode: bool = True
    supports_text: bool = True
    supports_image: bool = True
    supports_animation: bool = True
    supports_icon: bool = True
    supports_music: bool = True
    supports_jt: bool = True
    supports_flip: bool = False
    supports_clear: bool = False
    supports_countdown: bool = False
    #: Built-in display modes exposed as a "Display Mode" select. Maps an option
    #: key -> (send_command command, value) applied when that option is picked.
    display_modes: dict[str, tuple[str, object]] = {}
    #: Extra control commands routed through ``send_command`` and exposed via
    #: the ``ble_led_sign.send_command`` service (e.g. clock, scoreboard).
    extra_commands: tuple[str, ...] = ()

    # --- discovery ------------------------------------------------------
    @classmethod
    @abstractmethod
    def match(cls, service_info: BluetoothServiceInfoBleak) -> bool:
        """Return True if this advertisement belongs to the driver's family."""

    @classmethod
    @abstractmethod
    def parse(cls, service_info: BluetoothServiceInfoBleak) -> DeviceEntry:
        """Build a :class:`DeviceEntry` from a matching advertisement."""

    #: True if the panel size/capabilities must be read via an active
    #: connection (the advertisement does not carry them).
    requires_active_info: bool = False

    async def async_fetch_info(
        self, ble_device: BLEDevice, device: DeviceEntry, write_delay_ms: int = 0
    ) -> bool:
        """Query device metadata over a connection and update ``device`` in place."""
        return False

    # --- operations -----------------------------------------------------
    # Default implementations raise NotImplementedError; drivers override the
    # operations they actually support (and flip the matching capability flag).

    async def send_command(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        command: str,
        value: int | str | None = None,
    ) -> bool:
        raise NotImplementedError

    async def send_text(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        text: str,
        text_color: tuple[int, int, int] = (255, 255, 255),
        **options,
    ) -> bool:
        raise NotImplementedError

    async def send_image(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        image: Image.Image,
        threshold: int = 128,
        invert: bool = False,
        **options,
    ) -> bool:
        raise NotImplementedError

    async def send_animation(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        image_path: str,
        speed_ms: int | None = None,
        threshold: int = 128,
        invert: bool = False,
        **options,
    ) -> bool:
        raise NotImplementedError

    async def send_jt(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        jt_path: str,
    ) -> bool:
        raise NotImplementedError

    async def send_music(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        heights: list[int],
        colors: list[int],
    ) -> bool:
        raise NotImplementedError

    async def set_icon(
        self,
        ble_device: BLEDevice,
        device: DeviceEntry,
        password: str,
        write_delay_ms: int,
        icon_id: int,
    ) -> bool:
        raise NotImplementedError
