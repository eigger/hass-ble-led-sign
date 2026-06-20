"""Shared types for the BLE LED Sign integration."""

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .coordinator import BleLedSignPassiveBluetoothProcessorCoordinator

type BleLedSignConfigEntry = ConfigEntry[
    BleLedSignPassiveBluetoothProcessorCoordinator
]
