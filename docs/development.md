# Development & Real Home Assistant Testing

[English README](../README.md) · [한국어 README](../README.ko.md) · [Adoption Checklist](../ADOPTION_CHECKLIST.md)

This integration is distributed as a HACS custom integration via `custom_components/ble_led_sign/`. It conforms to Home Assistant Core component structure, config entry lifecycles, and public APIs.

## Architecture and Test Boundaries

- **Implementation**: Located under `custom_components/ble_led_sign/`, containing driver abstraction (`drivers/coolled`, `drivers/ipixel_color`), config flow, coordinator, entities (`light`, `number`, `select`, `switch`, `button`, `text`, `image`), and the declarative `renderer.py` module.
- **Tests**: Located in `tests/components/ble_led_sign/`, with common fixtures in `tests/conftest.py` (`auto_enable_custom_integrations`).
- **Real HA Fixtures**: Tests run against real Home Assistant core fixtures via `pytest-homeassistant-custom-component` (`hass`, `MockConfigEntry`), testing the component loader, entry setup/teardown, platform forward/unload, entity registry, device registry, and services.
- **Mock Boundary**: Only external Bluetooth hardware/GATT transport boundaries are mocked (`BleakTransport`). Driver protocol encoders, frame parsers, bitmap generators, `imagespec` layout rendering, and Home Assistant integration logic remain entirely real.

## Support Baselines and Current Testing

| Scope | Python | Home Assistant | pytest-homeassistant-custom-component | Declaration |
|---|---|---|---|---|
| Historical Support Baseline | 3.13 | 2025.1.0 | 0.13.201 | `hacs.json`, `requirements_test_min.txt` |
| Current Testing Target | 3.14 | 2026.10.2 | 0.13.373 | `requirements_test.txt` |

The historical minimum support baseline (`2025.1.0`) is preserved and separated from the current testing target. `requirements_test_min.txt` is excluded from automated dependency updates to prevent accidental version drift.

## Running Tests Locally

### Current Environment (Python 3.14 / HA 2026.10.2)

```bash
uv venv .venv --python 3.14
source .venv/bin/activate
uv pip install -r requirements_test.txt -r requirements_lint.txt "pillow>=10.0.0" "imagespec[datamatrix]>=1.1.0" "requests>=2.31.0"
pytest tests/components/ble_led_sign/ -v
uv pip check
```

### Minimum HA Environment (Python 3.13 / HA 2025.1.0)

```bash
uv venv .venv-min --python 3.13
source .venv-min/bin/activate
uv pip install --prerelease=allow -r requirements_test_min.txt -r requirements_lint.txt "pillow>=10.0.0" "imagespec[datamatrix]>=1.1.0" "requests>=2.31.0"
pytest tests/components/ble_led_sign/ -v
uv pip check
```

### Linting and Formatting

```bash
uv pip install -r requirements_lint.txt
ruff check .
ruff format --check .
```

## Dependencies & Manifest

- Runtime dependencies are declared in `manifest.json` (`pillow>=10.0.0`, `imagespec[datamatrix]>=1.1.0`, `requests>=2.31.0`).
- Home Assistant integration dependencies (`bluetooth_adapters`) and after-dependencies (`recorder`) are declared explicitly.
- Testing and linting tools are declared in dedicated `requirements_*.txt` files.
