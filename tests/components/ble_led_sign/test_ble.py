"""Real HA entry diagnostics and session transport failure contracts."""

import asyncio

import pytest
from blesession import ConnectFailed, NotificationTimeout, SessionDropped, WriteTimeout
from homeassistant.exceptions import HomeAssistantError

from custom_components.ble_led_sign.ble import async_send
from custom_components.ble_led_sign.const import DOMAIN
from custom_components.ble_led_sign.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.ble_led_sign.drivers import send_command, send_text
from custom_components.ble_led_sign.drivers.coolled.protocol import build_frame


async def command(hass, entry):
    return await async_send(
        hass,
        entry.entry_id,
        lambda args: send_command(*args, "turn_off"),
        operation="turn_off",
    )


async def test_failure_survives_recovery(hass, loaded_entry, transport, entity_id):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    transport.fail_connect = True
    with pytest.raises(HomeAssistantError):
        await command(hass, loaded_entry)
    reports = runtime["reports"]
    failure = dict(reports.last_failure)
    assert failure["failed_stage"] == "connect"
    assert reports.failures == 1
    assert reports.last_retry["retrying"]
    assert transport.connect_calls == 3
    transport.fail_connect = False
    await command(hass, loaded_entry)
    await hass.async_block_till_done()
    assert reports.last["success"]
    assert reports.last_failure == failure
    assert reports.failures == 1
    assert not transport.is_connected
    assert not runtime["connected"]
    state = hass.states.get(entity_id("sensor", "last_error"))
    assert state.state == "connect"
    assert state.attributes["error"] == failure["error"]
    assert hass.states.get(entity_id("binary_sensor", "connection")).state == "off"


async def test_unreachable_is_reported(hass, loaded_entry, monkeypatch):
    monkeypatch.setattr(
        "homeassistant.components.bluetooth.async_ble_device_from_address",
        lambda *a, **k: None,
    )
    with pytest.raises(HomeAssistantError):
        await command(hass, loaded_entry)
    report = hass.data[DOMAIN][loaded_entry.entry_id]["reports"].last_failure
    assert report["failed_stage"] == "unreachable"
    assert "connect_s" not in report


async def test_rejected_password_is_not_retried(
    hass, loaded_entry, transport, monkeypatch
):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    runtime["data"].device.requires_password = True

    async def reject(uuid, data, response=False):
        for handler in transport._handlers.values():
            handler(None, bytearray(build_frame(bytes([1]))))

    monkeypatch.setattr(transport, "write_gatt_char", reject)
    with pytest.raises(HomeAssistantError, match="Password verification"):
        await command(hass, loaded_entry)
    assert transport.connect_calls == 1
    assert runtime["reports"].last_failure["failed_stage"] == "auth"
    assert not transport.is_connected


async def test_drop_interrupts_ack_wait(hass, loaded_entry, transport, monkeypatch):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]

    async def drop(uuid, data, response=False):
        await transport.disconnect()

    monkeypatch.setattr(transport, "write_gatt_char", drop)
    with pytest.raises(HomeAssistantError) as error:
        await async_send(
            hass,
            loaded_entry.entry_id,
            lambda args: send_text(*args, "hello"),
            attempts=1,
        )
    assert isinstance(error.value.__cause__, SessionDropped)
    assert not runtime["connected"]
    assert runtime["reports"].failures == 1


@pytest.mark.parametrize("unload", [False, True])
async def test_cancel_and_unload_close_session(
    hass, loaded_entry, transport, monkeypatch, unload
):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    entered = asyncio.Event()

    async def hang(uuid, data, response=False):
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(transport, "write_gatt_char", hang)
    task = asyncio.create_task(command(hass, loaded_entry))
    await entered.wait()
    assert runtime["connected"]
    if unload:
        assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    else:
        task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not transport.is_connected
    assert not runtime["connected"]
    assert runtime["reports"].failures == 0
    assert runtime["reports"].last is None
    assert not runtime["session_tasks"]


async def test_report_failure_does_not_mask_success(hass, loaded_entry, monkeypatch):
    def broken(*args, **kwargs):
        raise ValueError("cannot resolve radio")

    monkeypatch.setattr("custom_components.ble_led_sign.ble.radio_facts", broken)
    assert await command(hass, loaded_entry)
    report = hass.data[DOMAIN][loaded_entry.entry_id]["reports"].last
    assert report["success"]


async def test_download_redacts_identity(hass, loaded_entry, transport):
    transport.fail_connect = True
    with pytest.raises(HomeAssistantError):
        await command(hass, loaded_entry)
    diagnostic = await async_get_config_entry_diagnostics(hass, loaded_entry)
    assert loaded_entry.unique_id not in str(diagnostic)
    assert diagnostic["last_failure"]["error"] == "**REDACTED**"
    assert diagnostic["last_failure"]["failed_stage"] == "connect"


async def test_ipixel_size_survives_advertisement(
    hass, loaded_ipixel_entry, ipixel_advertisement
):
    from custom_components.ble_led_sign import _async_fetch_device_info

    await _async_fetch_device_info(hass, loaded_ipixel_entry)
    data = hass.data[DOMAIN][loaded_ipixel_entry.entry_id]["data"]
    assert data.device.columns > 0
    dimensions = data.device.columns, data.device.rows
    data.update(ipixel_advertisement)
    assert (data.device.columns, data.device.rows) == dimensions


async def test_write_timeout_is_reported(hass, loaded_entry, transport, monkeypatch):
    from blesession import guarded_write

    async def short_write(*args, **kwargs):
        await guarded_write(*args, **kwargs, timeout=0.01)

    async def hang(*args, **kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(
        "custom_components.ble_led_sign.drivers.coolled.writer.guarded_write",
        short_write,
    )
    monkeypatch.setattr(transport, "write_gatt_char", hang)
    with pytest.raises(HomeAssistantError) as error:
        await command(hass, loaded_entry)
    assert isinstance(error.value.__cause__, WriteTimeout)
    assert not transport.is_connected
    assert (
        hass.data[DOMAIN][loaded_entry.entry_id]["reports"].last_failure["failed_stage"]
        == "transfer"
    )


async def test_password_silence_fails_auth(hass, loaded_entry, transport, monkeypatch):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    runtime["data"].device.requires_password = True

    async def silent(*args, **kwargs):
        pass

    monkeypatch.setattr(transport, "write_gatt_char", silent)
    monkeypatch.setattr(
        "custom_components.ble_led_sign.drivers.coolled.writer.RESPONSE_TIMEOUT_S", 0.01
    )
    with pytest.raises(HomeAssistantError) as error:
        await command(hass, loaded_entry)
    assert isinstance(error.value.__cause__, NotificationTimeout)
    assert runtime["reports"].last_failure["failed_stage"] == "auth"


async def test_retry_resolves_route_under_lock(hass, loaded_entry, monkeypatch):
    from custom_components.ble_led_sign.const import LOCK

    lock = hass.data[DOMAIN][LOCK]
    routes = []

    def lookup(*args):
        assert lock.locked()
        route = object()
        routes.append(route)
        return route

    async def sender(args):
        assert lock.locked()
        assert args[0] is routes[-1]
        if len(routes) == 1:
            raise ConnectFailed("temporary failure")
        return True

    monkeypatch.setattr(
        "custom_components.ble_led_sign.ble.ble_device_or_raise", lookup
    )
    monkeypatch.setattr(
        "custom_components.ble_led_sign.ble.radio_facts", lambda *args: {}
    )
    await async_send(hass, loaded_entry.entry_id, sender)
    assert len(routes) == 2
    assert not lock.locked()
    reports = hass.data[DOMAIN][loaded_entry.entry_id]["reports"]
    assert reports.last["success"]
    assert reports.last_retry["retrying"]
    assert reports.failures == 0
