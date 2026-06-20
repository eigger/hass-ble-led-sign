"""GATT identifiers and command bytes for the iPixel Color family.

These signs advertise as ``LED_BLE_*`` with the following services:

    Generic Access            0x1800
    Service 0x00FA
        0xFA02  WRITE, WRITE NO RESPONSE   (command write)
        0xFA03  NOTIFY                     (command notify, CCCD 0x2902)
    Service 0xAE00
        0xAE01  WRITE NO RESPONSE          (data write)
        0xAE02  NOTIFY                     (data notify, CCCD 0x2902)

Short control commands are written to ``0xFA02`` (see :mod:`.protocol` for the
frame layout); image / GIF / text use the windowed transfer in
:mod:`.protocol` and :mod:`.content`.
"""

from __future__ import annotations

# Advertised device name prefix.
DEVICE_NAME_PREFIXES: tuple[str, ...] = ("LED_BLE", "LED BLE")

# 16-bit primary services expanded to full 128-bit Bluetooth base UUIDs.
UUID_SERVICE_FA = "000000fa-0000-1000-8000-00805f9b34fb"
UUID_SERVICE_AE = "0000ae00-0000-1000-8000-00805f9b34fb"

# Service 0x00FA characteristics (control channel).
UUID_FA_WRITE = "0000fa02-0000-1000-8000-00805f9b34fb"
UUID_FA_NOTIFY = "0000fa03-0000-1000-8000-00805f9b34fb"

# Service 0xAE00 characteristics (bulk data channel, not yet used).
UUID_AE_WRITE = "0000ae01-0000-1000-8000-00805f9b34fb"
UUID_AE_NOTIFY = "0000ae02-0000-1000-8000-00805f9b34fb"

# Service UUIDs that identify the family during BLE discovery.
MATCH_SERVICE_UUIDS: frozenset[str] = frozenset({UUID_SERVICE_FA, UUID_SERVICE_AE})

MANUFACTURER = "iPixel Color"

# Control command bytes (command, subcommand).
CMD_POWER = 0x07
SUB_POWER = 0x01
CMD_BRIGHTNESS = 0x04
SUB_BRIGHTNESS = 0x80
CMD_DIY_MODE = 0x04
SUB_DIY_MODE = 0x01
CMD_TEXT_SPEED = 0x03
SUB_TEXT_SPEED = 0x01
CMD_DELETE_ALL = 0x03
SUB_DELETE_ALL = 0x80
CMD_EXIT = 0x01
SUB_EXIT = 0x01
CMD_FLIP = 0x06
SUB_FLIP = 0x80
CMD_SPORT = 0x06
SUB_SPORT = 0x00
CMD_CLOCK = 0x06
SUB_CLOCK = 0x01
CMD_WEEK = 0x12
SUB_WEEK = 0x80
CMD_RHYTHM = 0x00
SUB_RHYTHM = 0x02
CMD_RHYTHM_CHART = 0x01
SUB_RHYTHM_CHART = 0x02
CMD_COUNTDOWN = 0x0D
SUB_COUNTDOWN = 0x80
CMD_CHRONOGRAPH = 0x09
SUB_CHRONOGRAPH = 0x80
CMD_SCOREBOARD = 0x0A
SUB_SCOREBOARD = 0x80
CMD_PASSWORD_SET = 0x04
SUB_PASSWORD = 0x02
CMD_PASSWORD_VERIFY = 0x05
CMD_SET_TIME = 0x01
SUB_SET_TIME = 0x80
CMD_SHOW_SLOT = 0x08
SUB_SHOW_SLOT = 0x80
CMD_DELETE_SLOT = 0x02
SUB_DELETE_SLOT = 0x01

# Device-native brightness range (the app scales pixel data by value/100).
BRIGHTNESS_NATIVE_MIN = 1
BRIGHTNESS_NATIVE_MAX = 100

# Music equaliser: number of bars in the rhythm chart frame.
RHYTHM_CHART_BARS = 11

# The app raises the negotiated MTU after enabling notifications.
MTU_SIZE = 512
