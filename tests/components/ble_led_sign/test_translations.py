"""Translation files structural and key consistency tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

COMPONENT_DIR = (
    Path(__file__).resolve().parents[3] / "custom_components" / "ble_led_sign"
)
STRINGS = COMPONENT_DIR / "strings.json"
TRANSLATIONS = sorted((COMPONENT_DIR / "translations").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def key_paths(node, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Recursively return every leaf key path."""
    if not isinstance(node, dict):
        return {prefix}
    return {p for k, v in node.items() for p in key_paths(v, (*prefix, k))}


def test_translation_files_exist() -> None:
    """Ensure translations directory contains expected files."""
    assert TRANSLATIONS, "no translation files found"
    names = {p.name for p in TRANSLATIONS}
    assert "en.json" in names
    assert "ko.json" in names


@pytest.mark.parametrize("path", TRANSLATIONS, ids=lambda p: p.name)
def test_translation_keys_match_strings(path: Path) -> None:
    """Ensure all translation files cover keys present in strings.json."""
    strings_keys = key_paths(load(STRINGS))
    trans_keys = key_paths(load(path))
    missing = strings_keys - trans_keys
    assert not missing, (
        f"{path.name} is missing keys: {sorted('.'.join(m) for m in missing)}"
    )
