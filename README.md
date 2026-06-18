# hass-coolled
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=home-assistant)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/release/eigger/hass-coolled.svg)](https://github.com/eigger/hass-coolled/releases)
[![License](https://img.shields.io/github/license/eigger/hass-coolled)](https://github.com/eigger/hass-coolled/blob/main/LICENSE)
![integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=%24.coolled.total)

CoolLED BLE LED Sign Home Assistant Integration

## What Is a BLE LED Sign?

A **BLE LED sign** is a compact, battery-powered or USB-powered display that shows scrolling text, static messages, or simple graphics over **Bluetooth Low Energy (BLE)**.

Unlike traditional signs that require a dedicated mobile app for every update, this integration lets you control your sign directly from **Home Assistant** — automate messages, sync with sensors, and render rich layouts from YAML.

This project supports LED signs manufactured by **JTKJ** under the CoolLED and iLed product families.

## Key Characteristics

- 💡 **LED matrix display**
  - Bright, visible signage for indoor and outdoor use
- 📡 **Bluetooth Low Energy**
  - Wireless control without Wi-Fi on the device itself
- 🎨 **Flexible rendering**
  - Text, icons, QR codes, charts, and more via `coolled.write`
- ⚡ **Real-time control**
  - Power, brightness, scroll speed, and scroll mode from Home Assistant entities

## Why BLE LED Signs?

BLE LED signs are ideal for displaying information that:

- Needs to be visible at a glance
- Should update automatically from Home Assistant automations
- Lives in a location where a full display or wired setup is impractical

Common use cases include desk nameplates, shop window messages, event countdowns, and status boards driven by Home Assistant sensors.

## 💬 Feedback & Support

🐞 Found a bug? Let us know via an [Issue](https://github.com/eigger/hass-coolled/issues).  
💡 Have a question or suggestion? Join the [Discussion](https://github.com/eigger/hass-coolled/discussions)!

---

## Supported Devices

Devices are discovered automatically via BLE (Service UUID `0xFFF0`). Resolution and color capability are read from the advertisement scan record.

| Device Family | Example Names | Color Type | Notes |
|---------------|---------------|------------|-------|
| CoolLED 1248 | `CoolLED`, `CoolLEDA` | Single / Seven / Colorful | Classic matrix sign |
| CoolLED S / X | `CoolLEDS`, `CoolLEDX` | Varies | Password required |
| CoolLED M / U / UX | `CoolLEDM`, `CoolLEDU`, `CoolLEDUX` | Colorful | Password required, large MTU |
| CoolLED 536 | `CoolLED536` | Varies | — |
| iLed series | `iLedBike`, `iLedHat`, `iLedClock`, … | Varies | Some models require password |

Default resolution when scan data is unavailable: **48 × 12** pixels.

### Color Types

| Type | Label | Supported Payload Colors |
|------|-------|--------------------------|
| 0 | Single | `off`, `on`, `black`, `white` |
| 1 | Seven | Single + `red`, `yellow`, `green`, `cyan`, `blue`, `purple` |
| 2+ | Colorful | Seven + `orange`, `pink`, `#RRGGBB` (mapped to nearest) |

Device details (resolution, device ID, firmware, color type) appear under **Settings → Devices** after pairing.

## Entities

| Platform | Entity | Description |
|----------|--------|-------------|
| `light` | Display Power | Power on/off, brightness (10–255), scroll mode effect |
| `number` | Scroll Speed | Scroll speed (0–255) |
| `select` | Scroll Mode | `static`, `left`, `right`, `up`, `down`, `snowflake`, `picture`, `laser` |
| `text` | Scroll Text | Scrolling text (sent over BLE on change) |
| `image` | Last Sent Display | Last image successfully sent to the device |
| `image` | Render Preview | Preview from `dry_run` or last render |

## Installation

1. Install this integration with HACS (adding repository required), or copy the contents of this
repository into the `custom_components/coolled` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → CoolLED BLE Sign**.

## ⚠️ Important Notice

- It is **strongly recommended to use a Bluetooth proxy instead of a built-in Bluetooth adapter**.  
  Bluetooth proxies generally offer more stable connections and better range, especially in environments with multiple BLE devices.

> [!TIP]
> For hardware recommendations, refer to [Great ESP32 Board for an ESPHome Bluetooth Proxy](https://community.home-assistant.io/t/great-esp32-board-for-an-esphome-bluetooth-proxy/916767/31).  
- When using a Bluetooth proxy, it is strongly recommended to **keep the scan interval at its default value**.  
  Changing these values may cause issues with Bluetooth data transmission.
- **bluetooth_proxy:** must always have **active: true**.

  Example (recommended configuration with default values):

  ```yaml
  esp32_ble_tracker:
    scan_parameters:
      active: true

  bluetooth_proxy:
    active: true
  ```

## Options

After adding a device, configure options via **Settings → Devices & Services → CoolLED → Configure**:

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Device Password** | `000000` | 6 characters | Password for protected models (CoolLEDS, CoolLEDX, CoolLEDM, …) |
| **Retry Count** | 3 | 1–10 | Number of retry attempts when BLE write fails |
| **Packet Delay (ms)** | 15 | 0–1000 | Delay in milliseconds between each BLE packet |

> [!TIP]
> If you experience frequent write failures, try increasing the **Retry Count**.  
> If writes are unstable on larger payloads, try setting **Packet Delay** to 50–100 ms.

---

## Service: `coolled.write`

Renders a display image from payload elements and sends it to the sign. Colors are mapped to the device palette when rendering; seven-color and colorful devices transmit separate R, G, and B bitplanes.

### Service Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `payload` | ✅ | — | List of drawing elements (see [Payload Element Types](#payload-element-types)) |
| `rotate` | ❌ | `0` | Image rotation: `0`, `90`, `180`, `270` |
| `background` | ❌ | `black` | Background color (mapped to device palette) |
| `threshold` | ❌ | `128` | Luminance threshold for single-color bitmap encoding (`0`–`255`) |
| `invert` | ❌ | `false` | For single-color devices: when false, brighter pixels are lit |
| `dry_run` | ❌ | `false` | Generate preview image without sending to device |

### Basic Usage

```yaml
action: coolled.write
data:
  payload:
    - type: text
      value: Hello World!
      x: 2
      y: 1
      size: 10
      color: white
target:
  device_id: <your device>
```

### Rotation & Background

```yaml
action: coolled.write
data:
  rotate: 90
  background: black
  payload:
    - type: text
      value: Rotated!
      x: 2
      y: 1
      size: 10
      color: white
target:
  device_id: <your device>
```

### Dry Run (Preview Only)

> Preview image is available via the **Render Preview** image entity without sending data to the physical device.

```yaml
action: coolled.write
data:
  dry_run: true
  payload:
    - type: text
      value: Preview Test
      x: 2
      y: 1
      size: 10
      color: white
target:
  device_id: <your device>
```

---

## Service: `coolled.send_text`

Sends scrolling text directly to the sign (native text protocol). Seven-color devices use RGB bitplanes per character.

```yaml
action: coolled.send_text
data:
  text: Hello Home Assistant
  color: red
target:
  device_id: <your device>
```

---

## Service: `coolled.send_image`

Sends a local image file to the sign (resized, RGB bitplanes for color devices, chunked transfer).

```yaml
action: coolled.send_image
data:
  image_path: /config/www/sign.png
  threshold: 128
  invert: false
target:
  device_id: <your device>
```

---

## Service: `coolled.send_animation`

Sends an animated GIF to the sign.

```yaml
action: coolled.send_animation
data:
  image_path: /config/www/sign.gif
  speed_ms: 500
target:
  device_id: <your device>
```

---

## Service: `coolled.send_jt`

Sends a CoolLED JT program file (static graffiti or animation).

```yaml
action: coolled.send_jt
data:
  jt_path: /config/www/sign.jt
target:
  device_id: <your device>
```

---

## Service: `coolled.set_icon`

Shows a built-in icon by ID.

```yaml
action: coolled.set_icon
data:
  icon_id: 1
target:
  device_id: <your device>
```

---

## Service: `coolled.set_music`

Shows an 8-bar music equalizer pattern.

```yaml
action: coolled.set_music
data:
  heights: [4, 8, 12, 16, 12, 8, 4, 2]
  colors: [1, 2, 3, 4, 3, 2, 1, 1]
target:
  device_id: <your device>
```

---

### Payload Element Examples

> [!TIP]
> All elements support the `visible` field (`true`/`false`) to conditionally show or hide them.

> [!NOTE]
> **Color values** depend on the device's color type (see [Color Types](#color-types)).
> HEX strings (`#RRGGBB`) are accepted on colorful devices but will be **automatically mapped to the nearest supported color**.

#### text

```yaml
- type: text
  value: "Hello World!"
  x: 2
  y: 1
  size: 10
  color: white
  font: "NotoSansKR-Bold.ttf"
  anchor: lt            # Pillow anchor (e.g. lt, mt, rt, lm, mm, rm)
  align: left           # left, center, right
  spacing: 5
  stroke_width: 1
  stroke_fill: black
  max_width: 40         # Auto-wrap text within this pixel width
  rotation: 0           # Rotate text by angle (degrees counter-clockwise)
  background: "#333333" # Optional background color behind text
  background_padding: 2 # Padding around background (default: 2)
```

If `y` is omitted the element stacks below the previous element automatically (`y_padding` controls the gap, default `10`).

#### multiline

```yaml
- type: multiline
  value: "Line1;Line2;Line3"
  delimiter: ";"
  x: 2
  start_y: 1
  offset_y: 12
  size: 10
  font: "NotoSansKR-Regular.ttf"
  color: white
```

#### line

```yaml
- type: line
  x_start: 0
  x_end: 48
  y_start: 6
  y_end: 6
  fill: white
  width: 1
  dash: [4, 2]     # Optional: [on_px, off_px] for dashed/dotted lines
```

#### rectangle

```yaml
- type: rectangle
  x_start: 2
  y_start: 2
  x_end: 46
  y_end: 10
  fill: red
  outline: white
  width: 1
  radius: 2
```

#### icon

Uses [Material Design Icons](https://pictogrammers.com/library/mdi/). You can use the icon name with or without the `mdi:` prefix.

```yaml
- type: icon
  value: "weather-sunny"
  x: 2
  y: 1
  size: 12
  color: yellow
```

#### dlimg

Supports **HTTP/HTTPS URLs**, **local file paths**, and **Base64 data URIs**.

| `mode` | Description |
|--------|-------------|
| `stretch` | Stretch to fill exactly (default) |
| `fit` / `contain` | Scale preserving aspect ratio, pad with transparency |
| `fill` | Scale and crop to fill exactly, no padding |

```yaml
- type: dlimg
  url: "/config/www/images/logo.png"
  x: 0
  y: 0
  xsize: 48
  ysize: 12
  mode: fit
```

#### qrcode

```yaml
- type: qrcode
  data: "https://www.home-assistant.io"
  x: 20
  y: 0
  boxsize: 1
  border: 1
  color: white
  bgcolor: black
```

#### progress_bar

```yaml
- type: progress_bar
  x_start: 2
  y_start: 8
  x_end: 46
  y_end: 11
  progress: 75
  direction: right
  background: black
  fill: green
  outline: white
  width: 1
  show_percentage: false
```

#### plot

Reads entity history from **Home Assistant Recorder**.

```yaml
- type: plot
  data:
    - entity: sensor.temperature
      color: green
      width: 1
  duration: 3600
  x_start: 2
  y_start: 1
  x_end: 46
  y_end: 11
  size: 8
  font: "NotoSansKR-Regular.ttf"
```

For additional element types (`barcode`, `datamatrix`, `diagram`, `gauge`, `arc`, `polygon`, `table`, `text_box`, `rectangle_pattern`, `circle`, `ellipse`), see the [hass-gicisky README](https://github.com/eigger/hass-gicisky#payload-element-types) — the same payload schema is supported.

---

### Combined Example

```yaml
action: coolled.write
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
target:
  device_id: <your device>
```

---

## Payload Element Types

> [!TIP]
> All elements support the `visible` field (`true`/`false`, default: `true`) to conditionally show or hide them.

| **Type** | **Required Fields** | **Optional Fields** | **Description** |
|----------|---------------------|---------------------|-----------------|
| **text** | `x`, `value` | `y`, `size`(10), `font`, `color`(white), `anchor`(lt), `align`(left), `spacing`(5), `stroke_width`(0), `stroke_fill`(black), `max_width`, `y_padding`(10), `rotation`(0), `background`, `background_padding`(2) | Draws text. Auto-stacks if `y` omitted. |
| **multiline** | `x`, `value`, `delimiter`, `offset_y` | `start_y`, `size`(10), `font`, `color`, `anchor`(lm), `stroke_width`(0), `stroke_fill` | Splits text by delimiter and draws each line. |
| **line** | `x_start`, `x_end` | `y_start`, `y_end`, `fill`, `width`(1), `y_padding`(0), `dash` | Draws a straight line. |
| **rectangle** | `x_start`, `x_end`, `y_start`, `y_end` | `fill`, `outline`, `width`(1), `radius`(0), `corners`(all) | Draws a rectangle with optional rounded corners. |
| **rectangle_pattern** | `x_start`, `y_start`, `x_size`, `y_size`, `x_repeat`, `y_repeat`, `x_offset`, `y_offset` | `fill`, `outline`, `width`(1), `radius`(0), `corners`(all) | Repeated grid of rectangles. |
| **circle** | `x`, `y`, `radius` | `fill`, `outline`, `width`(1) | Draws a circle at center (`x`, `y`). |
| **ellipse** | `x_start`, `x_end`, `y_start`, `y_end` | `fill`, `outline`, `width`(1) | Draws an ellipse inside a bounding box. |
| **arc** | `x_start`, `y_start`, `x_end`, `y_end`, `start_angle`, `end_angle` | `fill`, `outline`, `width`(1), `pie`(false) | Draws an arc or filled pieslice. |
| **gauge** | `x`, `y`, `radius`, `progress` | `min_value`(0), `max_value`(100), `fill`, `background`, `outline`, `width`(8), `show_value`(false), `font`, `size`(16), `color` | Circular gauge (270° sweep). |
| **polygon** | `points` | `fill`, `outline`, `width`(1) | Draws a polygon. `points`: `"x1,y1;x2,y2;..."` format. |
| **table** | `x`, `y`, `columns`, `rows` | `header`(true), `header_fill`, `header_color`, `cell_color`, `cell_fill`, `border_color`, `border_width`(1), `row_height`, `padding`(4), `font`, `font_size`(14), `align`(left) | Draws a bordered table. |
| **text_box** | `x`, `y`, `value` | `size`(10), `font`, `padding`(5), `fill`, `color`, `outline`, `width`(1), `radius`(5) | Text inside a rounded background box. |
| **icon** | `x`, `y`, `value`, `size` | `color`/`fill`, `anchor`(la), `stroke_width`(0), `stroke_fill` | [Material Design Icons](https://pictogrammers.com/library/mdi/). |
| **dlimg** | `x`, `y`, `url`, `xsize`, `ysize` | `rotate`(0), `mode`(stretch) | Loads image from URL, local path, or Base64. |
| **qrcode** | `x`, `y`, `data` | `color`, `bgcolor`, `border`(1), `boxsize`(2) | Generates and embeds a QR code. |
| **barcode** | `x`, `y`, `data` | `color`, `bgcolor`, `code`(code128), `module_width`(0.2), `module_height`(7), `quiet_zone`(6.5), `font_size`(5), `text_distance`(5.0), `write_text`(true) | Draws various barcode formats. |
| **datamatrix** | `x`, `y`, `data` | `color`, `bgcolor`, `boxsize`(2) | DataMatrix 2D barcode. Requires `pyStrich`. |
| **diagram** | `x`, `y`, `height` | `width`(canvas), `margin`(20), `font`, `bars` | Bar chart. |
| **plot** | `data`([{`entity`}]) | `duration`(86400), `x_start`, `y_start`, `x_end`, `y_end`, `size`(10), `font`, `low`, `high`, `ylegend`, `yaxis`, `xlegend`, `debug`(false) | Time-series graph from HA Recorder. |
| **progress_bar** | `x_start`, `x_end`, `y_start`, `y_end`, `progress` | `direction`(right), `background`, `fill`, `outline`, `width`(1), `radius`(0), `show_percentage`(false) | Progress bar. |

---

## Fonts

The `text`, `multiline`, `diagram`, `plot`, and `table` elements accept a `font` field.

### Custom Fonts

Place `.ttf` font files in your Home Assistant `www/fonts` directory:

```
/config/www/fonts/NotoSansKR-Regular.ttf
```

Then reference them by filename:

```yaml
- type: text
  value: "Custom Font"
  x: 2
  y: 1
  size: 10
  font: "NotoSansKR-Regular.ttf"
  color: white
```

> [!NOTE]
> Fonts are loaded from `www/fonts/` in your Home Assistant config. Install the font files you need before using them in payloads.

---

## Limitations

- Seven-color and colorful devices encode graffiti/draw/animation data as separate R, G, and B bitplanes; single-color devices use one bitplane with a luminance threshold.
- Built-in icon IDs and music bar color indices are device-specific; experiment on your hardware.
- JT import supports `graffitiData` and `aniData` payloads from JT files.
- Program transfer for M/U/UX large-panel models may differ from 1248-class devices.
- CJK and emoji rendering depends on the fonts you provide.
- Verify behavior on your specific device model and firmware version.

---

## References

- [hass-gicisky](https://github.com/eigger/hass-gicisky) — shared renderer architecture and payload schema
- [Home Assistant Bluetooth](https://www.home-assistant.io/integrations/bluetooth/)
- [ESPHome Bluetooth Proxy](https://esphome.io/components/bluetooth_proxy.html)
