"""Test imagespec renderer integration for BLE LED signs."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.ble_led_sign.drivers.base import DeviceEntry
from custom_components.ble_led_sign.renderer import map_weather_icon, render_image


def test_map_weather_icon() -> None:
    """Test mapping weather icons to imagespec icons."""
    assert map_weather_icon("weather-clear-night") == "weather-night"
    assert map_weather_icon("weather-partlycloudy") == "weather-partly-cloudy"
    assert map_weather_icon("weather-exceptional") == "weather-sunny-off"
    assert map_weather_icon("weather-sunny") == "weather-sunny"
    assert map_weather_icon("other-icon") == "other-icon"


def test_render_image_simple(hass: HomeAssistant) -> None:
    """Test rendering a simple rectangle using imagespec."""
    device = DeviceEntry(
        name="TestSign",
        rows=32,
        columns=64,
        color_type=2,  # COLOR_TYPE_COLORFUL
    )

    service = MagicMock()
    service.data = {
        "payload": [
            {
                "type": "rectangle",
                "x_start": 0,
                "y_start": 0,
                "x_end": 10,
                "y_end": 10,
                "fill": "red",
            }
        ],
        "rotate": 0,
        "background": "black",
    }

    image = render_image("dummy_entity", device, service, hass)

    assert image is not None
    assert image.size == (64, 32)


def test_render_image_monochrome(hass: HomeAssistant) -> None:
    """Test rendering on a monochrome device."""
    device = DeviceEntry(
        name="MonoSign",
        rows=16,
        columns=32,
        color_type=0,  # COLOR_TYPE_SINGLE
    )

    service = MagicMock()
    service.data = {
        "payload": [
            {
                "type": "rectangle",
                "x_start": 0,
                "y_start": 0,
                "x_end": 15,
                "y_end": 15,
                "fill": "white",
            }
        ],
        "rotate": 0,
        "background": "black",
    }

    image = render_image("dummy_entity", device, service, hass)

    assert image is not None
    assert image.size == (32, 16)


def test_render_image_rotation(hass: HomeAssistant) -> None:
    """Test rendering with rotation."""
    device = DeviceEntry(
        name="RotateSign",
        rows=16,
        columns=32,
        color_type=1,
    )

    service = MagicMock()
    service.data = {
        "payload": [
            {
                "type": "rectangle",
                "x_start": 0,
                "y_start": 0,
                "x_end": 5,
                "y_end": 5,
                "fill": "green",
            }
        ],
        "rotate": 90,
        "background": "black",
    }

    image = render_image("dummy_entity", device, service, hass)

    assert image is not None
    assert image.size == (32, 16)


def test_render_image_weather_icon(hass: HomeAssistant) -> None:
    """Test rendering with a weather icon element."""
    device = DeviceEntry(
        name="IconSign",
        rows=16,
        columns=32,
        color_type=2,
    )

    service = MagicMock()
    service.data = {
        "payload": [
            {
                "type": "icon",
                "x": 0,
                "y": 0,
                "value": "weather-clear-night",
                "size": 16,
            }
        ],
        "rotate": 0,
        "background": "black",
    }

    image = render_image("dummy_entity", device, service, hass)
    assert image is not None
    assert image.size == (32, 16)


def test_render_image_error(hass: HomeAssistant) -> None:
    """Test rendering with invalid parameters raises HomeAssistantError."""
    device = DeviceEntry(
        name="ErrorSign",
        rows=32,
        columns=64,
        color_type=2,
    )

    service = MagicMock()
    service.data = {
        "payload": [
            {
                "type": "rectangle",
                "x_start": "invalid_value",
                "y_start": 0,
                "x_end": 10,
                "y_end": 10,
            }
        ],
        "rotate": 0,
        "background": "black",
    }

    with pytest.raises(HomeAssistantError):
        render_image("dummy_entity", device, service, hass)
