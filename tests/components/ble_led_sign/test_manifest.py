"""Manifest structure, fields, and Bluetooth matcher tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

MANIFEST_PATH = (
    Path(__file__).resolve().parents[3]
    / "custom_components"
    / "ble_led_sign"
    / "manifest.json"
)

ALLOWED_MATCHER_KEYS = {
    "connectable",
    "service_uuid",
    "service_data_uuid",
    "local_name",
    "manufacturer_id",
    "manufacturer_data_start",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_metadata(manifest: dict) -> None:
    """Verify standard manifest metadata fields."""
    assert manifest["domain"] == "ble_led_sign"
    assert manifest["name"] == "BLE LED Sign"
    assert manifest["config_flow"] is True
    assert manifest["codeowners"] == ["@eigger"]
    assert manifest["documentation"].startswith(
        "https://github.com/eigger/hass-ble-led-sign"
    )
    assert manifest["issue_tracker"].startswith(
        "https://github.com/eigger/hass-ble-led-sign/issues"
    )
    assert manifest["iot_class"] == "local_push"
    assert "version" in manifest

    assert "bluetooth_adapters" in manifest.get("dependencies", [])
    assert "recorder" in manifest.get("after_dependencies", [])


def test_manifest_requirements(manifest: dict) -> None:
    """Verify declared requirements."""
    reqs = manifest.get("requirements", [])
    assert any(r.startswith("imagespec") for r in reqs)
    assert any(r.startswith("pillow") for r in reqs)
    assert any(r.startswith("requests") for r in reqs)


def test_bluetooth_matchers(manifest: dict) -> None:
    """Verify Bluetooth discovery matchers conform to HA rules."""
    matchers = manifest.get("bluetooth", [])
    assert len(matchers) > 0

    uuid_re = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    for matcher in matchers:
        assert set(matcher).issubset(ALLOWED_MATCHER_KEYS)
        assert matcher.get("connectable") is True

        if "local_name" in matcher:
            name = matcher["local_name"]
            # Wildcard '*' or '[' must not appear in the first 3 characters
            prefix = name.rstrip("*")
            assert len(prefix) >= 3, f"Local name matcher '{name}' is too short"

        if "service_uuid" in matcher:
            assert uuid_re.match(matcher["service_uuid"]), (
                f"Invalid UUID: {matcher['service_uuid']}"
            )
