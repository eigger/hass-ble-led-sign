"""Device data holder, updated from BLE advertisements."""

from __future__ import annotations

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from .base import BaseLedDriver, DeviceEntry
from .registry import match_driver


class BleLedSignBluetoothDeviceData:
    """Holds the matched driver and parsed metadata for one BLE LED sign."""

    def __init__(self) -> None:
        self.driver: type[BaseLedDriver] | None = None
        self.device: DeviceEntry | None = None
        self.title: str | None = None
        self.last_rssi: int | None = None
        self.last_service_info: BluetoothServiceInfoBleak | None = None

    def supported(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Return True if any driver recognises this advertisement."""
        return match_driver(service_info) is not None

    def update(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Update device metadata from the latest advertisement."""
        self.last_service_info = service_info
        self.last_rssi = service_info.rssi

        driver = match_driver(service_info)
        if driver is None:
            return

        self.driver = driver
        self.device = driver.parse(service_info)
        identifier = service_info.address.replace(":", "")[-8:].upper()
        model = self.device.model if self.device else driver.name
        self.title = f"{identifier} ({model})"

    def get_device_name(self) -> str:
        if self.title:
            return self.title
        if self.device:
            return self.device.name
        return "BLE LED Sign"
