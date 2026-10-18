"""Test the BLE LED Sign config and options flows."""

from __future__ import annotations

from time import monotonic
from unittest.mock import patch

from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_led_sign.const import (
    CONF_DRIVER_ID,
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DOMAIN,
)

from .conftest import COOLLED_ADDRESS, COOLLED_NAME, _make_ble_device


async def test_bluetooth_discovery_flow(
    hass: HomeAssistant,
    enable_bluetooth: None,
    coolled_advertisement_data: AdvertisementData,
) -> None:
    """Test discovering a device directly over Bluetooth and confirming setup."""
    device = _make_ble_device(COOLLED_ADDRESS, COOLLED_NAME)
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        device,
        coolled_advertisement_data,
        monotonic(),
        True,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "custom_components.ble_led_sign.async_setup_entry", return_value=True
    ) as mock_setup:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert "CCDDEEFF" in result2["title"]
    assert result2["result"].unique_id == COOLLED_ADDRESS
    assert result2["result"].data.get(CONF_DRIVER_ID) == "coolled"
    assert len(mock_setup.mock_calls) == 1


async def test_bluetooth_discovery_in_progress(
    hass: HomeAssistant,
    enable_bluetooth: None,
    coolled_advertisement_data: AdvertisementData,
) -> None:
    """Test discovering an in-progress flow aborts with already_in_progress."""
    device = _make_ble_device(COOLLED_ADDRESS, COOLLED_NAME)
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        device,
        coolled_advertisement_data,
        monotonic(),
        True,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    # Second flow with the same device while first flow is open must abort
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_in_progress"


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
    coolled_advertisement_data: AdvertisementData,
) -> None:
    """Test discovering an already configured device aborts."""
    device = _make_ble_device(COOLLED_ADDRESS, COOLLED_NAME)
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        device,
        coolled_advertisement_data,
        monotonic(),
        True,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_bluetooth_discovery_not_supported(
    hass: HomeAssistant,
    enable_bluetooth: None,
) -> None:
    """Test discovering an unsupported Bluetooth device aborts."""
    unsupported_info = BluetoothServiceInfoBleak(
        name="UnknownDevice",
        address="99:88:77:66:55:44",
        rssi=-70,
        manufacturer_data={},
        service_data={},
        service_uuids=["00001234-0000-1000-8000-00805f9b34fb"],
        source="local",
        device=None,
        advertisement=None,
        connectable=True,
        time=0,
        tx_power=None,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=unsupported_info,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_user_flow_select_device(
    hass: HomeAssistant,
    advertisement: BluetoothServiceInfoBleak,
) -> None:
    """Test user initiation discovers available devices for selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.ble_led_sign.async_setup_entry", return_value=True
    ) as mock_setup:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ADDRESS: COOLLED_ADDRESS},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["result"].unique_id == COOLLED_ADDRESS
    assert len(mock_setup.mock_calls) == 1


async def test_user_flow_no_devices_found(hass: HomeAssistant) -> None:
    """Test user flow aborts when no BLE devices are discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_options_flow(
    hass: HomeAssistant,
    loaded_entry: MockConfigEntry,
) -> None:
    """Test updating integration options triggers reload listener."""
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    with patch.object(
        hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
    ) as mock_reload:
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_PASSWORD: "123456",
                CONF_RETRY_COUNT: 5,
                CONF_WRITE_DELAY_MS: 30,
            },
        )
        await hass.async_block_till_done()
        assert len(mock_reload.mock_calls) == 1

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert loaded_entry.options[CONF_PASSWORD] == "123456"
    assert loaded_entry.options[CONF_RETRY_COUNT] == 5
    assert loaded_entry.options[CONF_WRITE_DELAY_MS] == 30
