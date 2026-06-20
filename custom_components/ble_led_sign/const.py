"""Constants for the BLE LED Sign integration."""

from __future__ import annotations

DOMAIN = "ble_led_sign"
LOCK = "lock"
DEFAULT_NAME = "BLE LED Sign"
# Default manufacturer fallback for the device registry. Individual drivers may
# report their own manufacturer via ``DeviceEntry.manufacturer``.
MANUFACTURER = "JTKJ"

# CoolLED driver GATT identifiers.
UUID_SERVICE = "0000fff0-0000-1000-8000-00805f9b34fb"
UUID_CHAR = "0000fff1-0000-1000-8000-00805f9b34fb"

# Config entry data
CONF_DRIVER_ID = "driver_id"

# Options
CONF_PASSWORD = "password"
CONF_RETRY_COUNT = "retry_count"
CONF_WRITE_DELAY_MS = "write_delay_ms"
CONF_REQUEST_MTU = "request_mtu"

# Defaults
DEFAULT_PASSWORD = "000000"
DEFAULT_RETRY_COUNT = 3
DEFAULT_WRITE_DELAY_MS = 15
DEFAULT_REQUEST_MTU = True

# Protocol timing
PACKET_DELAY_MS = 15
RESPONSE_TIMEOUT_S = 5.0
MAX_PACKET_RETRIES = 3

# CoolLED 1248 devices expect the brightness value offset by 10
BRIGHTNESS_OFFSET = 10
BRIGHTNESS_MIN = 10
BRIGHTNESS_MAX = 255
SPEED_MIN = 0
SPEED_MAX = 255

# Scroll modes for CoolLED 1248 (1-indexed on wire)
MODES_1248: dict[int, str] = {
    1: "static",
    2: "left",
    3: "right",
    4: "up",
    5: "down",
    6: "snowflake",
    7: "picture",
    8: "laser",
}

COLOR_TYPE_SINGLE = 0
COLOR_TYPE_SEVEN = 1
COLOR_TYPE_COLORFUL = 2
COLOR_TYPE_COLORFUL_UX = 3
COLOR_TYPE_COLORFUL_CLOCK = 4

COLOR_TYPE_NAMES: dict[int, str] = {
    COLOR_TYPE_SINGLE: "single",
    COLOR_TYPE_SEVEN: "seven",
    COLOR_TYPE_COLORFUL: "colorful",
    COLOR_TYPE_COLORFUL_UX: "colorful_ux",
    COLOR_TYPE_COLORFUL_CLOCK: "colorful_clock",
}

COLOR_TYPE_LABELS: dict[int, str] = {
    COLOR_TYPE_SINGLE: "단색",
    COLOR_TYPE_SEVEN: "7색",
    COLOR_TYPE_COLORFUL: "풀컬러",
    COLOR_TYPE_COLORFUL_UX: "풀컬러 UX",
    COLOR_TYPE_COLORFUL_CLOCK: "풀컬러 시계",
}

DEVICE_NAME_PREFIXES: tuple[str, ...] = (
    "CoolLED",
    "CoolLEDA",
    "CoolLEDS",
    "CoolLEDM",
    "CoolLEDU",
    "CoolLEDUX",
    "CoolLED536",
    "CoolLEDX",
    "iLedBike",
    "iDevilEyes",
    "iLedHat",
    "iLedHatC",
    "iLedOpen",
    "iLedCar",
    "iLedClock",
    "iLedFitness",
)

# Device names that require password authentication after connect
PASSWORD_DEVICE_PREFIXES: tuple[str, ...] = (
    "CoolLEDS",
    "CoolLEDX",
    "CoolLEDM",
    "CoolLEDU",
    "CoolLEDUX",
    "iLedClock",
)

MTU_SIZE = 247
MTU_SPLIT_WRITE = 180
DEFAULT_SPLIT_WRITE = 20
TEXT_CHUNK_SIZE = 128

# Protocol command bytes (CoolLED 1248)
CMD_MUSIC = 0x01
CMD_TEXT = 0x02
CMD_DRAW = 0x03
CMD_ANIMATE = 0x04
CMD_ICON = 0x05

MUSIC_BAR_COUNT = 8
MAX_ANIMATION_FRAMES = 60
