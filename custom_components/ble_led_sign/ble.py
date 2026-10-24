"""Shared BLE attempts, session lifetime and diagnostic reports."""

from __future__ import annotations

import logging
from asyncio import current_task, gather, timeout
from contextlib import suppress
from contextvars import ContextVar
from typing import Any, NamedTuple
from weakref import WeakSet

from blesession import (
    DeviceError,
    SessionReports,
    SessionTrace,
    Unreachable,
    ble_session,
    fallback_report,
    report_attempt,
    run_attempts,
    still_up,
)
from blesession.hass import ble_device_or_raise, radio_facts
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_KEEP_CONNECTION,
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_KEEP_CONNECTION,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
    LOCK,
)

_LOGGER = logging.getLogger(__name__)


# Task-local context preserves the driver's BLEDevice API without shared mutable
# state between config entries or concurrent calls.
class _Active(NamedTuple):
    trace: SessionTrace
    status: Any
    runtime: dict
    keep: bool


_ACTIVE: ContextVar[_Active | None] = ContextVar("ble_led_sign_session", default=None)


class AuthenticationRejected(DeviceError):
    """A password retry cannot fix a rejected password."""

    stage = "auth"
    retryable = False


async def _drop_kept(runtime) -> None:
    """Close a link kept open between sends."""
    client = runtime.pop("client", None)
    runtime.pop("ble_device", None)
    if client is not None and client.is_connected:
        try:
            async with timeout(10):
                await client.disconnect()
        except Exception:  # noqa: BLE001 - the link is being abandoned anyway
            _LOGGER.debug("Closing the kept BLE link failed", exc_info=True)


async def run_protocol(ble_device, factory, action) -> bool:
    """Run a driver protocol with bounded connection cleanup and stage timings."""
    active = _ACTIVE.get()
    trace = active.trace if active else SessionTrace({"setup": "session"})
    status = active.status if active else lambda connected: None
    runtime = active.runtime if active else {}
    keep = bool(active and active.keep)
    try:
        async with ble_session(
            ble_device,
            trace=trace,
            max_attempts=1,
            disconnected_callback=lambda client: status(False),
            client=runtime.get("client"),
            keep=keep,
            # Clears a link a previous run left behind, e.g. after a HA restart.
            close_stale=keep,
        ) as client:
            # A kept link is reused by the next send instead of reconnecting.
            if keep:
                runtime["client"] = client
            status(True)
            protocol = factory(client, trace)
            with trace.timed("setup"):
                async with timeout(15):
                    await protocol.setup()
            with trace.timed("transfer"):
                await action(protocol)
            with trace.timed("finish"):
                await protocol.stop_notify()
        return True
    except BaseException:
        # Any failure drops the link, even one unrelated to the transport
        # (a rejected password leaves notifications half set up), so the next
        # send always starts from a clean GATT state.
        if keep:
            await _drop_kept(runtime)
        raise
    finally:
        status(keep and still_up(runtime.get("client")))


async def async_send(hass, entry_id, sender, *, operation="write", attempts=None):
    """Serialize one attempt at a time and retain every finished report."""
    runtime = hass.data[DOMAIN][entry_id]
    device = runtime["data"].device
    if device is None:
        raise HomeAssistantError("Device metadata is not ready yet")
    entry = hass.config_entries.async_get_entry(entry_id)
    options = {**entry.data, **entry.options} if entry else {}
    keep = bool(options.get(CONF_KEEP_CONNECTION, DEFAULT_KEEP_CONNECTION))
    retries = attempts or max(
        1, int(options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT))
    )
    coordinator = runtime["diagnostic_coordinator"]
    reports: SessionReports = runtime["reports"]

    def status(connected):
        runtime["connected"] = connected
        coordinator.async_set_updated_data(None)

    async def once(attempt):
        # Resolve the route after acquiring the lock on every retry.
        try:
            ble_device = ble_device_or_raise(hass, runtime["address"])
        except Unreachable:
            # A connected sign stops advertising, so Home Assistant forgets it
            # while we hold the link. Reuse the handle that link was made with.
            ble_device = runtime.get("ble_device")
            if not (keep and ble_device and still_up(runtime.get("client"))):
                # Otherwise release the link so the sign advertises again.
                await _drop_kept(runtime)
                raise
        if keep:
            runtime["ble_device"] = ble_device
        token = _ACTIVE.set(_Active(attempt.trace, status, runtime, keep))
        try:
            success = await sender(
                (
                    ble_device,
                    device,
                    options.get(CONF_PASSWORD, DEFAULT_PASSWORD),
                    int(options.get(CONF_WRITE_DELAY_MS, DEFAULT_WRITE_DELAY_MS)),
                )
            )
            if not success:
                raise DeviceError("The LED sign operation failed", stage="transfer")
            return True
        finally:
            _ACTIVE.reset(token)

    def record(attempt):
        try:
            report = report_attempt(
                attempt,
                operation=operation,
                attempts=retries,
                facts=radio_facts(hass, runtime["address"], attempt.trace.link),
                noun="LED sign",
            )
        except Exception:
            _LOGGER.debug("Unable to build BLE report; using fallback", exc_info=True)
            report = fallback_report(operation, attempt=attempt)
        reports.record(report)
        coordinator.async_set_updated_data(None)

    task = current_task()
    runtime["session_tasks"].add(task)
    try:
        last = await run_attempts(
            once,
            lock=hass.data[DOMAIN][LOCK],
            max_attempts=retries,
            on_attempt=record,
            stage_map={"setup": "session"},
        )
    finally:
        runtime["session_tasks"].discard(task)
    if last.error is not None:
        raise HomeAssistantError(str(last.error)) from last.error
    return True


async def async_stop_sessions(runtime):
    """Cancel queued and running work before dropping entry state."""
    tasks = list(runtime["session_tasks"])
    for task in tasks:
        task.cancel()
    await gather(*tasks, return_exceptions=True)
    await _drop_kept(runtime)


_MTU_REQUESTED: WeakSet = WeakSet()


async def request_mtu_once(client, size: int) -> None:
    """Exchange the MTU once per link; the ATT exchange is not repeatable."""
    with suppress(TypeError):  # a client that cannot be weak-referenced
        if client in _MTU_REQUESTED:
            return
        _MTU_REQUESTED.add(client)
    await client.request_mtu(size)
