"""Shared BLE attempts, session lifetime and diagnostic reports."""

from __future__ import annotations

import logging
from asyncio import current_task, gather, timeout
from contextlib import suppress
from contextvars import ContextVar

from blesession import (
    DeviceError,
    SessionReports,
    SessionTrace,
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
_ACTIVE: ContextVar[tuple | None] = ContextVar("ble_led_sign_session", default=None)


class AuthenticationRejected(DeviceError):
    """A password retry cannot fix a rejected password."""

    stage = "auth"
    retryable = False


async def _drop_kept(runtime) -> None:
    """Close a link kept open between sends."""
    client = runtime.pop("client", None)
    if client is not None and client.is_connected:
        with suppress(Exception):
            async with timeout(10):
                await client.disconnect()


async def run_protocol(ble_device, factory, action) -> bool:
    """Run a driver protocol with bounded connection cleanup and stage timings."""
    active = _ACTIVE.get()
    trace = active[0] if active else SessionTrace({"setup": "session"})
    status = active[1] if active else lambda connected: None
    runtime = active[2] if active else {}
    keep = bool(active and active[3])
    try:
        async with ble_session(
            ble_device,
            trace=trace,
            max_attempts=1,
            disconnected_callback=lambda client: status(False),
            client=runtime.get("client"),
            keep=keep,
        ) as client:
            # A kept link is reused by the next send instead of reconnecting.
            runtime["client"] = client if keep else None
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
        # A link left mid-transfer isn't safe for the next send.
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
        ble_device = ble_device_or_raise(hass, runtime["address"])
        token = _ACTIVE.set((attempt.trace, status, runtime, keep))
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
