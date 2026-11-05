<!-- hass-standards:header:start -->
# BLE LED Sign for Home Assistant

A Home Assistant custom integration that controls CoolLED, iLed and iPixel Color Bluetooth matrix LED displays, automating scrolling text, static messages, graphics and dynamic layouts.

**English** | [한국어](README.ko.md)

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-ble-led-sign?style=flat)](https://github.com/eigger/hass-ble-led-sign/releases)
[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5?style=flat)](#installation)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.1.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/tests.yml?branch=master&style=flat&label=Tests)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-ble-led-sign/validate.yml?branch=master&style=flat&label=Validate)](https://github.com/eigger/hass-ble-led-sign/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-ble-led-sign?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-ble-led-sign/latest/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-ble-led-sign/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

![LED Sign](custom_components/ble_led_sign/brand/logo.png)

## Supported devices

| Device family | Driver | Bluetooth Match | Highlights |
|---------------|--------|-----------------|------------|
| **CoolLED / iLed** | `coolled` | `CoolLED*`, `iLed*`, UUID `0xFFF0` | Full matrix control, 7-color / full RGB, animations, speed & brightness |
| **iPixel Color** | `ipixel_color` | `LED_BLE*`, UUID `0x00FA`, `0xAE00` | Real-time text, images, animations, clock/scoreboard control frames |

## Requirements

- **Home Assistant:** 2025.1.0 or later.
- **Bluetooth:** A local Bluetooth adapter or an ESPHome Bluetooth proxy with `active: true` configured.
- **Device:** A supported sign from [Supported devices](#supported-devices).

## Installation

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-ble-led-sign)
<!-- hass-standards:installation:end -->

1. Click the badge above to open the repository in Marketplace.
2. If you need to add it yourself, go to **Settings → Marketplace → Add from link** and enter <https://github.com/eigger/hass-ble-led-sign>. Connect GitHub if prompted.
3. Select **Install**. Restart Home Assistant if prompted, then continue to [Configuration](#configuration).

## Configuration

1. Under **Settings → Devices & services**, choose **Add integration → BLE LED Sign**, or configure it when discovered.
2. Select your sign from the list.

Use **Configure** to change [Device Password, Retry Count and Packet Delay](docs/user-guide.md#configuration-options) at any time.

## Quick start

Send a custom text message and icon using the `ble_led_sign.write` action:

```yaml
action: ble_led_sign.write
target:
  entity_id: light.ble_led_sign_display_power  # or device_id: <your_device_id>
data:
  payload:
    - type: text
      value: "Hello HA"
      x: 2
      y: 1
      size: 10
      color: cyan
    - type: icon
      value: "weather-sunny"
      x: 36
      y: 1
      size: 10
      color: yellow
```

## Important limitations

- **One connection at a time.** Close or disconnect vendor apps such as CoolLED1248 or iPixel Color before connecting from Home Assistant.
- **Packet loss.** BLE MTU limits and radio interference can cause failed writes for large images or animations. Increase **Retry Count** or **Packet Delay** if writes fail.

### Uninstall

Open the repository in Marketplace, then choose **⋮ → Uninstall**. Follow the prompts to remove any existing setup and restart Home Assistant if prompted.

## Documentation

- [User guide](docs/user-guide.md) — device profiles, color capabilities, entities, actions, animations and `imagespec` layouts.
- [Troubleshooting](docs/troubleshooting.md): Connection debugging, proxy setup, and diagnostic entities.
- [Development & Testing](docs/development.md): Development environment setup, test suite execution, and standards compliance.
- [Shared Bluetooth Proxy Guide](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md): Recommended ESPHome proxy hardware and configurations.
- [Payload action examples](docs/payload.md): Runnable layouts and device output settings.

<!-- hass-standards:support:start -->
## Support

- [Issues](https://github.com/eigger/hass-ble-led-sign/issues): Report bugs or request features.
- [Discussions](https://github.com/eigger/hass-ble-led-sign/discussions): Ask questions and share your experience.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## License

Released under the [MIT License](LICENSE).
<!-- hass-standards:license:end -->
