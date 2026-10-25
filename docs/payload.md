# Payloads

[README](../README.md) | **English** | [한국어](payload.ko.md)

## Common payload guide

Read the [imagespec payload guide](https://github.com/eigger/imagespec/blob/main/docs/payload.md) for drawing elements and shared properties.

## Using payloads in this integration

Call `ble_led_sign.write` from Developer Tools → Actions or an automation. Select the sign with `target.entity_id` or its device ID and provide the drawing list in `data.payload`. Home Assistant prepares templates before the integration uses the installed imagespec renderer. Existing device-specific examples remain in the [user guide](user-guide.md).

## Minimal working example

The [rectangle action](../examples/payload/minimal.yaml) draws a white rectangle on a black 48 × 12 single-color CoolLED display. The [template action](../examples/payload/template.yaml) renders the text `HA` through HA's actual template preparation. Both are complete action YAML; select your sign's actual light entity before use.

## Device output settings

The renderer uses the detected device's columns and rows. These examples use a CoolLED 12-row, 48-column single-color panel with black/off and white/on. Seven-color and RGB device families have different palettes; the driver maps and encodes them for the real panel. `data.rotate` accepts rotation degrees and keeps the canvas at the detected resolution (`rotate_mode: canvas`). `data.background` defaults to black. The bundled Galmuri14.ttf is the default font; the resolver also searches bundled font files and `www/fonts` in the HA configuration directory. Bitmap threshold and invert affect device encoding rather than the imagespec canvas.

## Supported features and limitations

Drawing elements, fonts and recorder history are provided through the integration's real imagespec context. History needs the real recorder integration and available recorded entities. HA resolves action templates, and the integration maps supported weather icons. The examples need no network, history or custom font. `dry_run: true` generates a preview without BLE output. Payload rendering does not add native scrolling or animations; use the driver's dedicated text/animation actions for those features. Physical dimensions and colors depend on the detected model; these examples do not establish every model's output.

## Troubleshooting

Check the [existing troubleshooting guide](troubleshooting.md), display dimensions, available fonts and the selected entity. Report problems through [Issues](https://github.com/eigger/hass-ble-led-sign/issues).
