"""CoolLED Bluetooth coordinator."""

from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.core import HomeAssistant

from .coolled_ble.parser import CoolledBluetoothDeviceData
from .types import CoolledConfigEntry


class CoolledPassiveBluetoothProcessorCoordinator(
    PassiveBluetoothProcessorCoordinator[None]
):
    """Passive BLE coordinator for CoolLED devices."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        address: str,
        mode: BluetoothScanningMode,
        update_method: Callable[[BluetoothServiceInfoBleak], None],
        device_data: CoolledBluetoothDeviceData,
        entry: CoolledConfigEntry,
        connectable: bool = True,
    ) -> None:
        super().__init__(hass, logger, address, mode, update_method, connectable)
        self.device_data = device_data
        self.entry = entry
