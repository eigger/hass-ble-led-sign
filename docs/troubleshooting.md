# BLE LED Sign Troubleshooting

[English README](../README.md) · [한국어](ko/troubleshooting.md) · [User Guide](user-guide.md)

Refer to the shared [Bluetooth proxy setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md#troubleshooting) guide for ESPHome configuration, proxy hardware recommendations (such as XIAO W5500 Ethernet Adapter V1.2 and M5Stack AtomS3U), and general Bluetooth troubleshooting.

## 1. Device Preparation

- **Power Supply**: Matrix LED signs draw substantial peak current. Use a dedicated 5V 2A+ USB power supply rather than low-power computer USB ports.
- **Disconnect Mobile Apps**: BLE peripherals only support a single concurrent central connection. If the vendor app (CoolLED1248, iPixel Color) is open on your smartphone, Home Assistant will fail to connect.
- **Range & Proxies**: Built-in server Bluetooth adapters often have poor range. We strongly recommend using an [ESPHome Bluetooth proxy](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md) with `active: true`.

## 2. Common Issues & Solutions

| Symptom | Cause & Recommended Action |
|---------|----------------------------|
| **Device not discovered** | Ensure the sign is powered and advertising. Check that your Bluetooth adapter or ESPHome proxy is online and within range. Verify the proxy scan mode is active. |
| **Connection fails or times out** | 1. Ensure smartphone apps are disconnected.<br>2. Check if your ESPHome proxy has reached its 3-connection limit.<br>3. In integration **Configure**, increase **Retry Count** from `3` to `5`. |
| **Packet loss or torn image rendering** | Large matrix payloads can overwhelm BLE buffers. In integration **Configure**, increase **Packet Delay (ms)** to `50`–`100` ms. |
| **Password authentication error** | Certain models (e.g. CoolLEDS, CoolLEDX) enforce a 6-digit password check. Set the matching password in integration **Configure** (default: `000000`). |
| **Panel size unknown / default 48×12** | Some families (like iPixel Color) do not advertise dimensions in scan packets. The integration queries panel size on first connection. Ensure the device is reachable to update the dimensions. |

## 3. Diagnostic Entities

Use Home Assistant entities to verify operation:

- `image.<device>_render_preview`: Displays the generated image when `dry_run: true` is used in `ble_led_sign.write`. Use this to test and inspect complex layouts before sending them over the air.
- `image.<device>_last_sent_display`: Displays the last successfully transmitted bitmap to confirm what is currently on the sign.

## 4. Reporting Issues

When reporting an issue on [GitHub Issues](https://github.com/eigger/hass-ble-led-sign/issues):

1. Enable debug logging in `configuration.yaml`:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.ble_led_sign: debug
   ```
2. Redact private information such as device MAC addresses or sensitive text payloads before posting logs.
3. Include your sign model, advertising name, adapter type (USB dongle vs. ESPHome proxy board), and Home Assistant version.
