from unittest.mock import MagicMock
import pytest
from homeassistant.exceptions import HomeAssistantError
from custom_components.ble_led_sign.renderer import render_image


def test_render_image_simple():
    # Arrange
    device = MagicMock()
    device.color_type = 2  # COLOR_TYPE_COLORFUL
    device.width = 64
    device.height = 32

    service = MagicMock()
    service.data = {
        "payload": [
            {"type": "rectangle", "x_start": 0, "y_start": 0, "x_end": 10, "y_end": 10, "fill": "red"}
        ],
        "rotate": 0,
        "background": "black"
    }

    hass = MagicMock()
    hass.config.path = MagicMock(return_value="/tmp/mock_fonts")

    # Act
    image = render_image("dummy_entity", device, service, hass)

    # Assert
    assert image is not None
    assert image.size == (64, 32)


def test_render_image_error():
    # Arrange
    device = MagicMock()
    device.color_type = 2
    device.width = 64
    device.height = 32

    service = MagicMock()
    # Invalid coordinates to trigger RenderError
    service.data = {
        "payload": [
            {"type": "rectangle", "x_start": "invalid", "y_start": 0, "x_end": 10, "y_end": 10}
        ],
        "rotate": 0,
        "background": "black"
    }

    hass = MagicMock()
    hass.config.path = MagicMock(return_value="/tmp/mock_fonts")

    # Act & Assert
    with pytest.raises(HomeAssistantError):
        render_image("dummy_entity", device, service, hass)
