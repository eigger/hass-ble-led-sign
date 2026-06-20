"""iPixel Color control command builders.

Each builder returns a control frame for characteristic 0xFA02. See
:mod:`.protocol` for the frame layout.
"""

from __future__ import annotations

from datetime import datetime

from .protocol import build_frame
from .const import (
    BRIGHTNESS_NATIVE_MAX,
    BRIGHTNESS_NATIVE_MIN,
    CMD_BRIGHTNESS,
    CMD_CHRONOGRAPH,
    CMD_CLOCK,
    CMD_COUNTDOWN,
    CMD_DELETE_ALL,
    CMD_DELETE_SLOT,
    CMD_DIY_MODE,
    CMD_EXIT,
    CMD_FLIP,
    CMD_PASSWORD_SET,
    CMD_PASSWORD_VERIFY,
    CMD_POWER,
    CMD_RHYTHM,
    CMD_RHYTHM_CHART,
    CMD_SCOREBOARD,
    CMD_SET_TIME,
    CMD_SHOW_SLOT,
    CMD_SPORT,
    CMD_TEXT_SPEED,
    CMD_WEEK,
    RHYTHM_CHART_BARS,
    SUB_BRIGHTNESS,
    SUB_CHRONOGRAPH,
    SUB_CLOCK,
    SUB_COUNTDOWN,
    SUB_DELETE_ALL,
    SUB_DELETE_SLOT,
    SUB_DIY_MODE,
    SUB_EXIT,
    SUB_FLIP,
    SUB_PASSWORD,
    SUB_POWER,
    SUB_RHYTHM,
    SUB_RHYTHM_CHART,
    SUB_SCOREBOARD,
    SUB_SET_TIME,
    SUB_SHOW_SLOT,
    SUB_SPORT,
    SUB_TEXT_SPEED,
    SUB_WEEK,
)


# --- power & brightness ------------------------------------------------------
def cmd_power(on: bool) -> bytes:
    """Power the display on/off (e.g. ``05 00 07 01 01``)."""
    return build_frame(CMD_POWER, SUB_POWER, 1 if on else 0)


def scale_brightness(ha_brightness: int) -> int:
    """Convert a Home Assistant brightness (0-255) to the device range (1-100)."""
    level = round((ha_brightness & 0xFF) / 255 * BRIGHTNESS_NATIVE_MAX)
    return max(BRIGHTNESS_NATIVE_MIN, min(BRIGHTNESS_NATIVE_MAX, level))


def cmd_brightness(ha_brightness: int) -> bytes:
    """Set brightness from a Home Assistant 0-255 value (e.g. ``05 00 04 80 32``)."""
    return build_frame(CMD_BRIGHTNESS, SUB_BRIGHTNESS, scale_brightness(ha_brightness))


# --- display behaviour -------------------------------------------------------
def cmd_diy_mode(mode: int) -> bytes:
    """Select a built-in (DIY) display mode (``05 00 04 01 <mode>``)."""
    return build_frame(CMD_DIY_MODE, SUB_DIY_MODE, mode)


def cmd_text_speed(speed: int) -> bytes:
    """Set scroll/text speed (``05 00 03 01 <speed>``)."""
    return build_frame(CMD_TEXT_SPEED, SUB_TEXT_SPEED, speed)


def cmd_flip(flipped: bool) -> bytes:
    """Flip the display upside down (``05 00 06 80 <isDown>``)."""
    return build_frame(CMD_FLIP, SUB_FLIP, 1 if flipped else 0)


def cmd_delete_all() -> bytes:
    """Clear all stored content (``04 00 03 80``)."""
    return build_frame(CMD_DELETE_ALL, SUB_DELETE_ALL)


def cmd_exit() -> bytes:
    """Exit the current mode (``04 00 01 01``)."""
    return build_frame(CMD_EXIT, SUB_EXIT)


# --- timers, clock, scoreboard ----------------------------------------------
def _now_date_fields() -> tuple[int, int, int, int]:
    now = datetime.now()
    # The app sends weekday as ISO (1=Mon … 7=Sun).
    return now.year - 2000, now.month, now.day, now.isoweekday()


def cmd_clock(mode: int, time_scale: bool = True, show_date: bool = False) -> bytes:
    """Show the clock face (``0B 00 06 01 …``) using the current date/time.

    ``time_scale`` true sends 0 (12h tick marks), false sends 1, matching the
    app's ``sendColockMode`` logic.
    """
    year, month, day, week = _now_date_fields()
    return build_frame(
        CMD_CLOCK,
        SUB_CLOCK,
        mode,
        0 if time_scale else 1,
        1 if show_date else 0,
        year,
        month,
        day,
        week,
    )


def cmd_week(week: int | None = None) -> bytes:
    """Set the device weekday (``05 00 12 80 <week>``)."""
    if week is None:
        week = datetime.now().isoweekday()
    return build_frame(CMD_WEEK, SUB_WEEK, week)


def cmd_sport(mode: int, speed: int, decimal: int) -> bytes:
    """Send pedometer/sport data (``07 00 06 00 <mode> <speed> <decimal>``)."""
    return build_frame(CMD_SPORT, SUB_SPORT, mode, speed, decimal)


def cmd_countdown(flag: int, minutes: int, seconds: int) -> bytes:
    """Control the countdown timer (``07 00 0D 80 <flag> <min> <sec>``)."""
    return build_frame(CMD_COUNTDOWN, SUB_COUNTDOWN, flag, minutes, seconds)


def cmd_chronograph(flag: int) -> bytes:
    """Control the stopwatch/chronograph (``05 00 09 80 <flag>``)."""
    return build_frame(CMD_CHRONOGRAPH, SUB_CHRONOGRAPH, flag)


def cmd_scoreboard(score1: int, score2: int) -> bytes:
    """Set the two scoreboard counters (``08 00 0A 80 <s1_hi s1_lo s2_hi s2_lo>``)."""
    return build_frame(
        CMD_SCOREBOARD,
        SUB_SCOREBOARD,
        (score1 >> 8) & 0xFF,
        score1 & 0xFF,
        (score2 >> 8) & 0xFF,
        score2 & 0xFF,
    )


# --- music / equaliser -------------------------------------------------------
def cmd_rhythm(level: int, mode: int) -> bytes:
    """Set a single music rhythm level (``06 00 00 02 <level> <mode>``)."""
    return build_frame(CMD_RHYTHM, SUB_RHYTHM, level, mode)


def cmd_rhythm_chart(mode: int, levels: list[int]) -> bytes:
    """Set the 11-bar music equaliser (``10 00 01 02 <mode> + 11 bytes``).

    Each input sample (0-255) is mapped to a 1-15 bar height, matching the
    app's ``sendRhythmChart`` scaling.
    """
    bars = [0] * RHYTHM_CHART_BARS
    for i, value in enumerate(levels[:RHYTHM_CHART_BARS]):
        scaled = (value & 0xFF) * 15 // 255
        magnitude = abs(scaled)
        if 1 <= magnitude < 16:
            bars[i] = scaled
        elif magnitude != 0:
            bars[i] = 15
        else:
            bars[i] = 1
    return build_frame(CMD_RHYTHM_CHART, SUB_RHYTHM_CHART, mode, *bars)


# --- password ----------------------------------------------------------------
def _password_bytes(password: str) -> list[int]:
    """Split a 6-digit password into three byte pairs (matches the app)."""
    pwd = (password or "000000")[:6].rjust(6, "0")
    return [int(pwd[0:2]), int(pwd[2:4]), int(pwd[4:6])]


def cmd_password_set(flag: int, password: str) -> bytes:
    """Set the device password (``08 00 04 02 <flag> p0 p1 p2``)."""
    return build_frame(CMD_PASSWORD_SET, SUB_PASSWORD, flag, *_password_bytes(password))


def cmd_password_verify(password: str) -> bytes:
    """Verify the device password (``07 00 05 02 p0 p1 p2``)."""
    return build_frame(CMD_PASSWORD_VERIFY, SUB_PASSWORD, *_password_bytes(password))


# --- time & slots ------------------------------------------------------------
def cmd_set_time(
    hour: int | None = None, minute: int | None = None, second: int | None = None
) -> bytes:
    """Set the device RTC (``08 00 01 80 hh mm ss 00``); defaults to now."""
    now = datetime.now()
    hour = now.hour if hour is None else hour
    minute = now.minute if minute is None else minute
    second = now.second if second is None else second
    return build_frame(CMD_SET_TIME, SUB_SET_TIME, hour, minute, second, 0)


def cmd_show_slot(number: int) -> bytes:
    """Display a saved slot (``07 00 08 80 01 00 <n>``)."""
    return build_frame(CMD_SHOW_SLOT, SUB_SHOW_SLOT, 0x01, 0x00, number)


def cmd_delete_slot(number: int) -> bytes:
    """Delete a saved slot (``07 00 02 01 01 00 <n>``)."""
    return build_frame(CMD_DELETE_SLOT, SUB_DELETE_SLOT, 0x01, 0x00, number)
