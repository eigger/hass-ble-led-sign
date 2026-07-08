# hass-ble-led-sign
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=home-assistant)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/release/eigger/hass-ble-led-sign.svg)](https://github.com/eigger/hass-ble-led-sign/releases)
[![License](https://img.shields.io/github/license/eigger/hass-ble-led-sign)](https://github.com/eigger/hass-ble-led-sign/blob/main/LICENSE)
![integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=%24.ble_led_sign.total)

BLE LED Sign — a unified Home Assistant integration for BLE LED signs

## What is a BLE LED sign?

A **BLE LED sign** is a compact matrix display controlled over **Bluetooth Low Energy**. Automate scrolling text, static messages, and simple graphics from Home Assistant instead of a vendor app.

The integration uses a **driver architecture**: each device family lives under `custom_components/ble_led_sign/drivers/` and shares the same entities and services. Shipped drivers:

| Driver | Devices | Highlights |
|--------|---------|------------|
| `coolled` | CoolLED / iLed (JTKJ) | Full matrix control, JT import, native text/draw/animation |
| `ipixel_color` | `LED_BLE_*` (iPixel Color) | Control commands + PNG/GIF/text transfer, device slots |

Default resolution when scan data is unavailable: **48 × 12** pixels.

### Color types

| Type | Label | Payload colors |
|------|-------|----------------|
| 0 | Single | `off`, `on`, `black`, `white` |
| 1 | Seven | Single + `red`, `yellow`, `green`, `cyan`, `blue`, `purple` |
| 2+ | Colorful | Seven + `orange`, `pink`, `#RRGGBB` (mapped to nearest) |

Resolution, firmware, and color type appear under **Settings → Devices** after pairing.

## Feedback & Support

- Found a bug? [Open an issue](https://github.com/eigger/hass-ble-led-sign/issues)
- Questions or ideas? [Join the discussion](https://github.com/eigger/hass-ble-led-sign/discussions)

---

## Supported devices

| Device family | Driver | Match | Notes |
|---------------|--------|-------|-------|
| CoolLED 1248 | `coolled` | `CoolLED`, `CoolLEDA` / UUID `0xFFF0` | Classic matrix sign |
| CoolLED S / X | `coolled` | `CoolLEDS`, `CoolLEDX` | Password required |
| CoolLED M / U / UX | `coolled` | `CoolLEDM`, `CoolLEDU`, `CoolLEDUX` | Password, large MTU |
| CoolLED 536 | `coolled` | `CoolLED536` | — |
| iLed series | `coolled` | `iLedBike`, `iLedHat`, `iLedClock`, … | Some models need password |
| iPixel Color | `ipixel_color` | `LED_BLE*` / UUID `0x00FA`, `0xAE00` | Commands + image/GIF/text |

## Entities

Created **only for capabilities the matched driver supports**:

| Platform | Entity | Description |
|----------|--------|-------------|
| `light` | Display Power | Power and brightness; scroll mode as effect when supported |
| `number` | Scroll Speed | Scroll speed (0–255) |
| `select` | Scroll Mode | `static`, `left`, `right`, `up`, `down`, `snowflake`, `picture`, `laser` |
| `switch` | Flip Display | Flip upside down |
| `button` | Clear Display | Clear stored content |
| `text` | Scroll Text | Scrolling text (sent on change) |
| `image` | Last Sent Display | Last image successfully sent |
| `image` | Render Preview | Preview from `dry_run` or last render |

**CoolLED** exposes the full set where hardware allows. **iPixel Color** uses `send_image` / `send_animation` / `send_text` for content and `ble_led_sign.send_command` for clock, scoreboard, countdown, DIY mode, and other control frames.

## Installation

1. Install with HACS (custom repository required), or copy this repo into `custom_components/ble_led_sign`.
2. Restart Home Assistant.
3. Add **BLE LED Sign** via **Settings → Devices & Services → Add Integration**.

## Important Notice

Use a **Bluetooth proxy** instead of a built-in adapter when possible — especially with multiple BLE devices nearby.

> [!TIP]
> Hardware recommendations: [Great ESP32 Board for an ESPHome Bluetooth Proxy](https://community.home-assistant.io/t/great-esp32-board-for-an-esphome-bluetooth-proxy/916767/31)

Keep the proxy scan interval at its default. **`bluetooth_proxy` must have `active: true`.**

```yaml
esp32_ble_tracker:
  scan_parameters:
    active: true

bluetooth_proxy:
  active: true
```

## Options

Configure via **Settings → Devices & Services → BLE LED Sign → Configure**:

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Device Password** | `000000` | 6 chars | Password for protected CoolLED / iLed models |
| **Retry Count** | 3 | 1–10 | Retries when a BLE write fails |
| **Packet Delay (ms)** | 15 | 0–1000 | Delay between BLE packets |

> [!TIP]
> Unstable writes: increase **Retry Count** or set **Packet Delay** to 50–100 ms for large payloads.

---

## Payload & rendering (`imagespec`)

From version 2.0.0, `ble_led_sign.write` renders with **[imagespec](https://github.com/eigger/imagespec)** — a declarative YAML list of drawing elements encoded and sent to the sign.

**Documentation (maintained in imagespec, not duplicated here):**

| Topic | Link |
|-------|------|
| Element examples with preview images | [imagespec/docs/elements.md](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| All element fields & defaults | [imagespec README — Element Reference](https://github.com/eigger/imagespec#elements-reference) |
| Layout, palette, LLM authoring guide | [imagespec/docs/authoring.md](https://github.com/eigger/imagespec/blob/main/docs/authoring.md) |

**BLE LED Sign-specific behaviour:**

- **Resolution:** `width` and `height` come from the **device profile** (columns × rows), not the service call.
- **Palette:** depends on device color type (see [Color types](#color-types)). Off-palette colors are quantized.
- **Rotation:** `rotate: 90/180/270` uses **canvas mode** — fixed panel size, background rotates.
- **Default font:** `Galmuri14.ttf` (bundled). Custom fonts also work from `www/fonts/`.
- **`plot` element:** reads history from Home Assistant **Recorder**.
- **`icon` element:** Home Assistant `weather-*` icon names are mapped automatically.
- **Encoding:** seven-color and colorful devices send separate R/G/B bitplanes; single-color devices use one bitplane with `threshold` / `invert`.
- **Layout:** prefer `row` / `column` / `stack` over hand-placed coordinates.
- **Image entities:** **Last Sent Display** and **Render Preview** (`dry_run`).

---

## Services

### `ble_led_sign.write`

Renders payload elements and sends the bitmap to the sign.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `payload` | yes | — | List of [imagespec elements](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| `rotate` | no | `0` | `0`, `90`, `180`, or `270` |
| `background` | no | `black` | Mapped to device palette |
| `threshold` | no | `128` | Luminance threshold for single-color encoding (`0`–`255`) |
| `invert` | no | `false` | Single-color: when false, brighter pixels are lit |
| `dry_run` | no | `false` | Render only; updates **Render Preview** without BLE send |

```yaml
action: ble_led_sign.write
target:
  device_id: <your device>
data:
  payload:
    - type: text
      value: Hello World!
      x: 2
      y: 1
      size: 10
      color: white
```

Preview:

```yaml
action: ble_led_sign.write
target:
  device_id: <your device>
data:
  dry_run: true
  payload:
    - type: text
      value: Preview Test
      x: 2
      y: 1
      size: 10
      color: white
```

Combined example:

```yaml
action: ble_led_sign.write
target:
  device_id: <your device>
data:
  background: black
  payload:
    - type: text
      value: "Home Status"
      x: 2
      y: 1
      size: 10
      color: white
    - type: line
      x_start: 0
      x_end: 48
      y_start: 12
      y_end: 12
      fill: white
      width: 1
    - type: icon
      value: thermometer
      x: 2
      y: 4
      size: 10
      color: red
    - type: text
      value: "{{ states('sensor.temperature') }}°C"
      x: 14
      y: 4
      size: 10
      color: green
    - type: progress_bar
      x_start: 2
      y_start: 9
      x_end: 46
      y_end: 11
      progress: "{{ states('sensor.humidity') | int }}"
      direction: right
      fill: cyan
```

### Other services

| Service | Purpose |
|---------|---------|
| `ble_led_sign.send_text` | Native scrolling text (`text`, `color`, `animation`, `speed`, `rainbow`, `bg_color`, `font`, `save_slot`) |
| `ble_led_sign.send_image` | Local image file (`image_path`, `threshold`, `invert`, `save_slot`) |
| `ble_led_sign.send_animation` | Animated GIF (`image_path`, `speed_ms`, `threshold`, `invert`, `save_slot`) |
| `ble_led_sign.send_jt` | CoolLED JT program file (`jt_path`) |
| `ble_led_sign.set_icon` | Built-in icon by ID (`icon_id`) |
| `ble_led_sign.set_music` | 8-bar equalizer (`heights`, `colors`) |
| `ble_led_sign.send_command` | iPixel control commands (`command`, `value`) — clock, scoreboard, countdown, flip, DIY mode, slots, … |

**iPixel Color** examples:

```yaml
# Scrolling text with device-side animation
action: ble_led_sign.send_text
target:
  device_id: <your device>
data:
  text: Hello Home Assistant
  color: red
  animation: 1
  speed: 80

# Save to device slot 3, recall later with show_slot
action: ble_led_sign.send_image
target:
  device_id: <your device>
data:
  image_path: /config/www/sign.png
  save_slot: 3

action: ble_led_sign.send_command
target:
  device_id: <your device>
data:
  command: show_slot
  value: 3

# Scoreboard: team scores 3 and 1
action: ble_led_sign.send_command
target:
  device_id: <your device>
data:
  command: scoreboard
  value: [3, 1]
```

---

## Fonts

- **`ble_led_sign.write` payloads:** default `Galmuri14.ttf` from `custom_components/ble_led_sign/fonts/galmuri/`. Also checks `www/fonts/`.
- **`ble_led_sign.send_text` (iPixel):** bundled **Galmuri** pixel font (Hangul + Latin, SIL OFL 1.1 — see `fonts/galmuri/LICENSE.txt`). Override with the `font` field.

```yaml
- type: text
  value: "Custom Font"
  x: 2
  y: 1
  size: 10
  font: "NotoSansKR-Regular.ttf"
  color: white
```

Place custom `.ttf` files in `config/www/fonts/`.

---

## Adding a driver

1. Create `drivers/<family>/` with `driver.py` subclassing `BaseLedDriver`.
2. Implement `match()`, `parse()`, and supported operations; set `supports_*` flags.
3. Register in `drivers/registry.py` (`DRIVERS`).
4. Add BLE matchers to `manifest.json`.

Entities and services call dispatch helpers in `drivers/__init__.py` — they never talk to a protocol directly.

---

## Limitations

- Seven-color and colorful devices encode draw/animation data as separate R/G/B bitplanes; single-color devices use one bitplane with `threshold`.
- Built-in icon IDs and music bar color indices are device-specific.
- JT import supports `graffitiData` and `aniData` payloads.
- Program transfer for M/U/UX large panels may differ from 1248-class devices.
- CJK and emoji rendering depends on fonts you provide.
- Verify behavior on your specific model and firmware.

---

## References

- [imagespec](https://github.com/eigger/imagespec) — rendering engine
- [Home Assistant Bluetooth](https://www.home-assistant.io/integrations/bluetooth/)
- [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy.html)
