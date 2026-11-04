# BLE LED Sign brand assets

An original geometric LED matrix sign icon drawn by `scripts/generate_brand.py`
on a dark navy rounded square, with a matching gold `LED Sign` wordmark for the
landscape logo. No third-party artwork is used.

| File | Size | Purpose |
| --- | --- | --- |
| `icon.png` | 256 × 256 | Home Assistant and HACS icon |
| `icon@2x.png` | 512 × 512 | High-resolution icon |
| `logo.png` | 937 × 256 | Landscape integration logo; README artwork |
| `logo@2x.png` | 1874 × 512 | High-resolution landscape logo |

All images are RGBA PNGs with transparent outer corners and backgrounds. These
sizes follow the [HA brand image guidelines](https://contributors.home-assistant.io/core/integrations/brands/).
Home Assistant 2026.3 and later serves these assets from the integration's local
`brand/` directory. The gold wordmark works against light and dark backgrounds,
so separate dark variants are not required.

## Source and permission

The icon is drawn from geometric primitives in this repository's
`scripts/generate_brand.py` and is covered by the repository's MIT license
(Copyright (c) 2026 eigger). The wordmark is rendered with Pillow's bundled
Aileron Regular via
[`ImageFont.load_default`](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.load_default).
[Aileron](https://dotcolon.net/font/aileron/) permits commercial use and is
released with no rights reserved. No font file is redistributed or loaded from
the system.

## Reproduce

Use Python 3.10 or newer and Pillow 12.3.0 (also supplied by HA 2026.10.2):

```sh
python -m pip install Pillow==12.3.0
python scripts/generate_brand.py
```

The script needs no network access and produces the same PNG bytes on every
run with that Pillow version.

SHA256 (Pillow 12.3.0):

- `icon@2x.png`: `f98ddaf3524c0f424acdfe0d1ebfee6761d964e09b3c8f7618bff73d00e77a21`
- `icon.png`: `4889411760b25a5251dc92de9a39a936f66db42714ec7dfcd97a3aa065538204`
- `logo@2x.png`: `52ee853614eab0ca37b2ab8889dc9490c5cfe15bfa9412564e411845146b9f6e`
- `logo.png`: `2e59304d293b1d3f6b2a1cb432be3d94c54a80a6e1896a922b77dff81f727289`

The local `brand/icon.png` is used by the
[HACS brands check](https://hacs.xyz/docs/publish/include/#check-brands).
These files do not imply inclusion in the HACS default list or HA brands
repository. README pages use `custom_components/ble_led_sign/brand/logo.png`.
