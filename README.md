# BLE LED Sign

<!-- hass-standards:badges:start -->
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](#installation)
[![Release](https://img.shields.io/github/v/release/eigger/hass-ble-led-sign?style=flat-square)](https://github.com/eigger/hass-ble-led-sign/releases)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.1.0-41BDF5?style=flat-square)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/tests.yml?branch=master&style=flat-square&label=Tests)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/validate.yml?branch=master&style=flat-square&label=Validate)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-ble-led-sign?style=flat-square)](LICENSE)
[![Analytics reporting installs](https://img.shields.io/badge/dynamic/json?style=flat-square&color=41BDF5&label=Usage&query=%24.ble_led_sign.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io/)
<!-- hass-standards:badges:end -->

**English** | [한국어](README.ko.md)

BLE LED Sign is a unified Home Assistant integration for controlling Bluetooth Low Energy (BLE) matrix LED displays (CoolLED, iLed, iPixel Color). Automate scrolling text, static messages, graphics, and dynamic layouts from Home Assistant instead of vendor mobile apps.

## Supported devices

The integration uses a modular driver architecture supporting multiple hardware families:

| Device family | Driver | Bluetooth Match | Highlights |
|---------------|--------|-----------------|------------|
| **CoolLED / iLed** | `coolled` | `CoolLED*`, `iLed*`, UUID `0xFFF0` | Full matrix control, 7-color / full RGB, animations, speed & brightness |
| **iPixel Color** | `ipixel_color` | `LED_BLE*`, UUID `0x00FA`, `0xAE00` | Real-time text, images, animations, clock/scoreboard control frames |

Full hardware details and color capabilities are documented in the [User Guide](docs/user-guide.md).

## Requirements

- **Home Assistant**: `2025.1.0` or newer.
- **Bluetooth**: A local Bluetooth adapter or an [ESPHome Bluetooth proxy](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md) with `active: true` configured.

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant and select **Integrations**.
2. Click the top-right menu and choose **Custom repositories**.
3. Add repository URL `https://github.com/eigger/hass-ble-led-sign` with category **Integration**.
4. Search for **BLE LED Sign**, click **Download**, and restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/ble_led_sign` folder from this repository into your Home Assistant `<config_dir>/custom_components/` directory.
2. Restart Home Assistant.

To remove, delete `custom_components/ble_led_sign` and restart Home Assistant.

## Configuration

1. In Home Assistant, navigate to **Settings → Devices & Services**.
2. Click **Add Integration** and search for **BLE LED Sign** (or click Configure if discovered automatically).
3. Select your discovered sign from the list.
4. Optional settings such as **Device Password**, **Retry Count**, and **Packet Delay** can be adjusted at any time via **Configure**. See [Configuration Options](docs/user-guide.md#configuration-options) for details.

## Quick start

Send a custom text message and icon using the `ble_led_sign.write` action:

```yaml
action: ble_led_sign.write
target:
  device_id: <your_device_id>
data:
  payload:
    - icon:
        name: weather-sunny
        color: yellow
    - text:
        content: " Hello Home Assistant!"
        color: cyan
```

For more examples, animations, and image rendering syntax, refer to the [User Guide](docs/user-guide.md).

## Important limitations

- **Single Connection Only**: BLE LED signs only support one active connection at a time. Vendor mobile apps (CoolLED1248, iPixel Color) must be fully closed/disconnected for Home Assistant to connect.
- **Packet Transmission**: Due to BLE MTU limitations, large matrix drawings or animations may experience packet drops on high-noise environments. If writes fail, increase **Retry Count** or **Packet Delay** in the integration options.
- Review [Troubleshooting](docs/troubleshooting.md) for diagnostic procedures and connection fixes.

## Documentation

- [User Guide](docs/user-guide.md): Comprehensive device profiles, entity catalog, service reference, and `imagespec` declarative layouts.
- [Troubleshooting](docs/troubleshooting.md): Connection debugging, proxy setup, and diagnostic entities.
- [Development & Testing](docs/development.md): Development environment setup, test suite execution, and standards compliance.
- [Shared Bluetooth Proxy Guide](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md): Recommended ESPHome proxy hardware and configurations.

## Support

- Report bugs or unexpected behavior via [GitHub Issues](https://github.com/eigger/hass-ble-led-sign/issues).
- Questions and feature discussions are welcome on [GitHub Discussions](https://github.com/eigger/hass-ble-led-sign/discussions).

## License

This project is licensed under the [MIT License](LICENSE).
