"""Driver registry: discovery matching and lookup by id."""

from __future__ import annotations

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from .base import BaseLedDriver
from .coolled import CoolledDriver
from .ipixel_color import IpixelColorDriver

# Order matters: the first driver whose ``match`` returns True wins. Keep the
# more specific families before broader catch-alls.
DRIVERS: tuple[type[BaseLedDriver], ...] = (
    CoolledDriver,
    IpixelColorDriver,
)

_BY_ID: dict[str, type[BaseLedDriver]] = {driver.driver_id: driver for driver in DRIVERS}
_INSTANCES: dict[str, BaseLedDriver] = {}


def match_driver(
    service_info: BluetoothServiceInfoBleak,
) -> type[BaseLedDriver] | None:
    """Return the first driver class that recognises this advertisement."""
    for driver in DRIVERS:
        if driver.match(service_info):
            return driver
    return None


def get_driver(driver_id: str) -> BaseLedDriver:
    """Return a cached driver instance for the given id."""
    if driver_id not in _INSTANCES:
        driver_cls = _BY_ID.get(driver_id)
        if driver_cls is None:
            raise KeyError(f"Unknown driver id: {driver_id!r}")
        _INSTANCES[driver_id] = driver_cls()
    return _INSTANCES[driver_id]
