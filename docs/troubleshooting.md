# BLE LED Sign Troubleshooting

[English README](../README.md) · [한국어](troubleshooting.ko.md) · [User Guide](user-guide.md)

## Common troubleshooting

See the shared [Bluetooth troubleshooting](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.md) and [proxy setup guide](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md).

## Device-specific checks

- **Power Supply**: Matrix LED signs draw substantial peak current. Use the rated power supply for your panel; high-current panels may need a dedicated 5V 2A or larger supply.
- **Disconnect Mobile Apps**: These signs commonly allow only one controller at a time; connection capacity depends on firmware. If the vendor app (CoolLED1248, iPixel Color) is open on your smartphone, Home Assistant will fail to connect.
- **Range & Proxies**: Built-in server Bluetooth adapters often have poor range. We strongly recommend using an [ESPHome Bluetooth proxy](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md) with `active: true`.

## Symptoms and actions

| Symptom | Failing stage | Checks | Action |
|---|---|---|---|
| Device not discovered | unreachable | Power, advertisement reception, adapter/proxy online | Move the sign closer and close the vendor app. Passive discovery supports active GATT; active scan mode is not required by this integration. |
| Connection fails | connect | Other apps holding a link, available proxy slots | Close CoolLED1248/iPixel Color and check proxy capacity. Retry Count controls total attempts. |
| Password rejected | auth | Password-protected CoolLED model | Set the matching six-digit password (default `000000`). A rejection is not retried. |
| Packet loss or torn image | transfer | Panel power and radio path | Increase Packet Delay to 50–100 ms if needed; this is an integration option, not a proxy scan setting. |
| Dimensions unknown | transfer / device_info | iPixel Color does not advertise panel size | A successful query supplies dimensions. A timeout remains an error; a later advertisement can trigger another query. |
| Command sent but display unchanged | transfer / finish | Some short commands have no device completion ACK | A successful write confirms transport completion, not a physical display readback. |

## Diagnostics and logs

Sessions connect on demand and disconnect after each operation. The **BLE connection** diagnostic is on only while a GATT session is held; off between operations is expected.

**Last operation** exposes the latest report. **Last error stage**, **Last failure**, and **Failure count** preserve final failure evidence across later successes. Counts reset on reload; retry attempts are retained separately in the diagnostic download and do not increase the final failure count. Cancellation does not count as failure.

Report attributes include `operation`, `success`, `failed_stage`, `failed_detail`, `error`, timings, and available radio facts (`via`, `via_type`, `rssi`, `paths`, `via_unconfirmed`). A route with `via_unconfirmed: true` is an advertisement-based estimate. Reports are frozen after each attempt. Home Assistant's integration diagnostics download removes radio names and free-text errors; entity attributes may still contain addresses or names, so redact them before sharing.

Notification setup/MTU negotiation is bounded at 15 seconds. Each GATT write is bounded at 10 seconds; response waits retain the protocol limits. There is no overall image/animation timeout. Sessions release the shared lock between retries. Disconnect cleanup is bounded by blesession.

Use Home Assistant image entities to inspect rendered content:

- `image.<device>_render_preview`: Displays the generated image when `dry_run: true` is used in `ble_led_sign.write`. Use this to test and inspect complex layouts before sending them over the air.
- `image.<device>_last_sent_display`: Displays the last successfully transmitted bitmap to confirm what is currently on the sign.

## If the problem persists

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

Include integration, blesession and ESPHome versions, panel/proxy models and revisions, connection method, failure time/stage and reproduction steps. Collect only the reproduction interval, turn debug logging off afterwards, and remove addresses, passwords, tokens and personal sign content. Local/proxy hardware and the Home Assistant UI have not been validated by this change.
