"""iPixel Color command frames."""

import pytest

from custom_components.ble_led_sign.drivers.ipixel_color.commands import cmd_show_slot
from custom_components.ble_led_sign.drivers.ipixel_color.writer import build_command


def test_show_slot_single() -> None:
    assert cmd_show_slot(3) == bytes([7, 0, 8, 0x80, 1, 0, 3])


def test_show_slot_playlist() -> None:
    assert cmd_show_slot([1, 2, 3]) == bytes([9, 0, 8, 0x80, 3, 0, 1, 2, 3])


def test_show_slot_service_value() -> None:
    assert build_command("show_slot", 2) == cmd_show_slot(2)
    assert build_command("show_slot", [1, 2]) == cmd_show_slot([1, 2])


def test_show_slot_empty() -> None:
    with pytest.raises(ValueError):
        cmd_show_slot([])


def test_show_slot_none_defaults_to_zero() -> None:
    assert build_command("show_slot", None) == cmd_show_slot(0)


def test_show_slot_string_values() -> None:
    assert build_command("show_slot", "3") == cmd_show_slot(3)
    assert build_command("show_slot", ["1", "2"]) == cmd_show_slot([1, 2])


def test_show_slot_empty_list_via_service() -> None:
    with pytest.raises(ValueError):
        build_command("show_slot", [])


@pytest.mark.parametrize("bad", [-1, 256, [1, 256]])
def test_show_slot_out_of_range(bad) -> None:
    with pytest.raises(ValueError):
        cmd_show_slot(bad)


def test_show_slot_too_many() -> None:
    with pytest.raises(ValueError):
        cmd_show_slot(list(range(15)))
