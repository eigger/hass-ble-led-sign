"""Real Home Assistant fixtures and deterministic external BLE transport."""

from __future__ import annotations

from time import monotonic
from typing import Any

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError
from habluetooth import get_manager
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_led_sign.const import (
    CONF_DRIVER_ID,
    DOMAIN,
    UUID_CHAR,
    UUID_SERVICE,
)
from custom_components.ble_led_sign.drivers.coolled.protocol import build_frame

COOLLED_ADDRESS = "AA:BB:CC:DD:EE:FF"
COOLLED_NAME = "CoolLED_1248"

IPIXEL_ADDRESS = "11:22:33:44:55:66"
IPIXEL_NAME = "LED_BLE_5566"


class BleakTransport:
    """Emulate external GATT boundary without mocking Home Assistant core."""

    def __init__(self) -> None:
        self.is_connected = False
        self.fail_connect = False
        self.writes: list[tuple[str, bytes, bool]] = []
        self._handlers: dict[str, Any] = {}

    async def connect(self, *_args, **_kwargs) -> BleakTransport:
        if self.fail_connect:
            raise BleakError("Connection failed")
        self.is_connected = True
        return self

    async def disconnect(self) -> None:
        self.is_connected = False

    async def start_notify(self, char_specifier: Any, callback: Any) -> None:
        self._handlers[str(char_specifier).lower()] = callback

    async def stop_notify(self, char_specifier: Any) -> None:
        self._handlers.pop(str(char_specifier).lower(), None)

    async def write_gatt_char(
        self, char_specifier: Any, data: bytes, response: bool = False
    ) -> None:
        uuid = str(char_specifier).lower()
        packet = bytes(data)
        self.writes.append((uuid, packet, response))
        # If CoolLED and notification registered, send password/command ack
        if uuid == UUID_CHAR.lower() and uuid in self._handlers:
            self._handlers[uuid](None, bytearray(build_frame(bytes([0x00]))))
        # If iPixel Color bulk transfer and notify registered, send window ack
        fa_notify = "0000fa03-0000-1000-8000-00805f9b34fb"
        if (
            uuid == "0000fa02-0000-1000-8000-00805f9b34fb"
            and fa_notify in self._handlers
        ):
            self._handlers[fa_notify](None, bytearray([0x05, 0x00, 0x00, 0x00, 0x00]))

    async def request_mtu(self, mtu: int) -> int:
        return mtu

    def clear(self) -> None:
        self.writes.clear()


@pytest.fixture
def transport(monkeypatch: pytest.MonkeyPatch) -> BleakTransport:
    fake_client = BleakTransport()

    async def fake_establish(_client_cls, ble_device, *args, **kwargs):
        if fake_client.fail_connect:
            raise BleakError("Cannot connect to BLE device")
        await fake_client.connect()
        return fake_client

    monkeypatch.setattr(
        "custom_components.ble_led_sign.drivers.coolled.writer.establish_connection",
        fake_establish,
    )
    monkeypatch.setattr(
        "custom_components.ble_led_sign.drivers.ipixel_color.writer.establish_connection",
        fake_establish,
    )
    return fake_client


@pytest.fixture
def coolled_advertisement_data() -> AdvertisementData:
    return AdvertisementData(
        local_name=COOLLED_NAME,
        manufacturer_data={},
        service_data={},
        service_uuids=[UUID_SERVICE],
        tx_power=None,
        rssi=-55,
        platform_data=(),
    )


def _make_ble_device(address: str, name: str, rssi: int = -55) -> BLEDevice:
    try:
        return BLEDevice(address, name, {}, rssi)
    except TypeError:
        return BLEDevice(address, name, {})


@pytest.fixture
async def advertisement(
    hass: HomeAssistant,
    enable_bluetooth: None,
    coolled_advertisement_data: AdvertisementData,
) -> BluetoothServiceInfoBleak:
    """Feed a CoolLED scan result through the real HA Bluetooth manager."""
    device = _make_ble_device(COOLLED_ADDRESS, COOLLED_NAME)
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        device,
        coolled_advertisement_data,
        monotonic(),
        True,
    )
    get_manager().scanner_adv_received(info)
    await hass.async_block_till_done()
    return info


@pytest.fixture
def ipixel_advertisement_data() -> AdvertisementData:
    return AdvertisementData(
        local_name=IPIXEL_NAME,
        manufacturer_data={},
        service_data={},
        service_uuids=["000000fa-0000-1000-8000-00805f9b34fb"],
        tx_power=None,
        rssi=-60,
        platform_data=(),
    )


@pytest.fixture
async def ipixel_advertisement(
    hass: HomeAssistant,
    enable_bluetooth: None,
    ipixel_advertisement_data: AdvertisementData,
) -> BluetoothServiceInfoBleak:
    """Feed an iPixel Color scan result through the real HA Bluetooth manager."""
    device = _make_ble_device(IPIXEL_ADDRESS, IPIXEL_NAME)
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        device,
        ipixel_advertisement_data,
        monotonic(),
        True,
    )
    get_manager().scanner_adv_received(info)
    await hass.async_block_till_done()
    return info


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=COOLLED_ADDRESS,
        title=COOLLED_NAME,
        data={
            "address": COOLLED_ADDRESS,
            CONF_DRIVER_ID: "coolled",
        },
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
async def loaded_entry(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    transport: BleakTransport,
    advertisement: BluetoothServiceInfoBleak,
) -> MockConfigEntry:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
def ipixel_entry(hass: HomeAssistant) -> MockConfigEntry:
    config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=IPIXEL_ADDRESS,
        title=IPIXEL_NAME,
        data={
            "address": IPIXEL_ADDRESS,
            CONF_DRIVER_ID: "ipixel_color",
        },
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
async def loaded_ipixel_entry(
    hass: HomeAssistant,
    ipixel_entry: MockConfigEntry,
    transport: BleakTransport,
    ipixel_advertisement: BluetoothServiceInfoBleak,
) -> MockConfigEntry:
    assert await hass.config_entries.async_setup(ipixel_entry.entry_id)
    await hass.async_block_till_done()
    return ipixel_entry


@pytest.fixture
def entity_id(hass: HomeAssistant):
    from homeassistant.helpers import entity_registry as er

    def lookup(domain: str, translation_key: str | None = None) -> str:
        registry = er.async_get(hass)
        entries = er.async_entries_for_config_entry(
            registry,
            next(e.entry_id for e in hass.config_entries.async_entries(DOMAIN)),
        )
        for entity in entries:
            if entity.domain == domain:
                if translation_key is None or entity.translation_key == translation_key:
                    return entity.entity_id
        raise KeyError(f"Entity not found: {domain=} {translation_key=}")

    return lookup
