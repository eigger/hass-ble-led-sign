"""The CoolLED Bluetooth integration."""

from __future__ import annotations

import logging
from asyncio import Lock
from functools import partial
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from PIL import Image

from .const import (
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
    LOCK,
    MANUFACTURER,
)
from .coordinator import CoolledPassiveBluetoothProcessorCoordinator
from .device import sync_device_registry
from .coolled_ble import (
    CoolledBluetoothDeviceData,
    send_animation,
    send_image,
    send_jt,
    send_music,
    send_text,
    set_icon,
)
from .coolled_ble.text import image_file_to_png_bytes, image_to_draw_bytes, resolve_text_color
from .renderer import render_image
from .services import SERVICE_NAMES
from .types import CoolledConfigEntry

PLATFORMS: list[Platform] = [
    Platform.IMAGE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
]

_LOGGER = logging.getLogger(__name__)


def process_service_info(
    hass: HomeAssistant,
    entry: CoolledConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Update device metadata from BLE advertisements."""
    entry.runtime_data.device_data.update(service_info)
    sync_device_registry(hass, entry, service_info)


async def async_setup_entry(hass: HomeAssistant, entry: CoolledConfigEntry) -> bool:
    """Set up CoolLED from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if LOCK not in hass.data[DOMAIN]:
        hass.data[DOMAIN][LOCK] = Lock()

    address = entry.unique_id
    assert address is not None

    data = CoolledBluetoothDeviceData()
    hass.data[DOMAIN][entry.entry_id] = {
        "address": address,
        "data": data,
        "image_coordinator": DataUpdateCoordinator(hass, _LOGGER, name=f"{DOMAIN}_image"),
        "preview_coordinator": DataUpdateCoordinator(hass, _LOGGER, name=f"{DOMAIN}_preview"),
    }

    device_registry = dr.async_get(hass)
    identifier = address.replace(":", "")[-8:].upper()
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(CONNECTION_BLUETOOTH, address)},
        manufacturer=MANUFACTURER,
        name=f"CoolLED {identifier}",
    )
    hass.data[DOMAIN][entry.entry_id]["device_id"] = device_entry.id

    bt_coordinator = CoolledPassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=partial(process_service_info, hass, entry),
        device_data=data,
        connectable=True,
        entry=entry,
    )
    entry.runtime_data = bt_coordinator

    async def send_text_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _send_text_to_device)

    async def send_image_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _send_image_to_device)

    async def send_animation_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _send_animation_to_device)

    async def send_jt_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _send_jt_to_device)

    async def set_icon_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _set_icon_on_device)

    async def set_music_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _set_music_on_device)

    async def write_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _write_label_to_device)

    for service_name in SERVICE_NAMES:
        handler = {
            "write": write_service,
            "send_text": send_text_service,
            "send_image": send_image_service,
            "send_animation": send_animation_service,
            "send_jt": send_jt_service,
            "set_icon": set_icon_service,
            "set_music": set_music_service,
        }[service_name]
        hass.services.async_register(DOMAIN, service_name, handler)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(bt_coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CoolledConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if unload_ok and len(hass.config_entries.async_entries(DOMAIN)) == 0:
        for service in SERVICE_NAMES:
            hass.services.async_remove(DOMAIN, service)
    return unload_ok


def _normalize_device_ids(service: ServiceCall) -> list[str]:
    if service.target and service.target.device_id:
        device_ids = service.target.device_id
        if isinstance(device_ids, str):
            return [device_ids]
        return list(device_ids)
    device_ids = service.data.get("device_id")
    if isinstance(device_ids, str):
        return [device_ids]
    if device_ids:
        return list(device_ids)
    return []


async def _run_for_devices(
    hass: HomeAssistant,
    service: ServiceCall,
    callback,
) -> None:
    device_ids = _normalize_device_ids(service)
    if not device_ids:
        raise HomeAssistantError("device_id is required")

    for device_id in device_ids:
        entry_id = _get_entry_id_from_device(hass, device_id)
        await callback(hass, entry_id, service)


def _get_entry_id_from_device(hass: HomeAssistant, device_id: str) -> str:
    for entry_id, runtime in hass.data.get(DOMAIN, {}).items():
        if entry_id == LOCK:
            continue
        if isinstance(runtime, dict) and runtime.get("device_id") == device_id:
            return entry_id
    raise HomeAssistantError(f"No CoolLED entry found for device_id {device_id!r}")


def _get_options(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    entry = hass.config_entries.async_get_entry(entry_id)
    return {**(entry.data if entry else {}), **(entry.options if entry else {})}


async def _render_label(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> tuple[Image.Image, bytes]:
    runtime = hass.data[DOMAIN][entry_id]
    data: CoolledBluetoothDeviceData = runtime["data"]
    device = data.device
    if device is None:
        raise HomeAssistantError("Device metadata is not ready yet")

    image = await hass.async_add_executor_job(
        render_image, entry_id, device, service, hass
    )
    png_bytes = await hass.async_add_executor_job(image_file_to_png_bytes, image)
    runtime["preview_coordinator"].async_set_updated_data(png_bytes)
    return image, png_bytes


async def _write_label_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    dry_run = service.data.get("dry_run", False)
    threshold = int(service.data.get("threshold", 128))
    invert = service.data.get("invert", False)

    image, png_bytes = await _render_label(hass, entry_id, service)
    runtime = hass.data[DOMAIN][entry_id]
    device = runtime["data"].device
    assert device is not None
    _ = image_to_draw_bytes(
        image,
        device.columns,
        device.rows,
        threshold=threshold,
        invert=invert,
        color_type=device.color_type,
    )

    if dry_run:
        return

    async with hass.data[DOMAIN][LOCK]:
        success = await _ble_send(
            hass,
            entry_id,
            lambda args: send_image(
                args[0],
                args[1],
                args[2],
                args[3],
                image,
                threshold=threshold,
                invert=invert,
            ),
        )
        if success:
            runtime["image_coordinator"].async_set_updated_data(png_bytes)


async def _send_text_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    text = service.data.get("text")
    if not text:
        raise HomeAssistantError("text is required")

    runtime = hass.data[DOMAIN][entry_id]
    device = runtime["data"].device
    if device is None:
        raise HomeAssistantError("Device metadata is not ready yet")

    text_color = resolve_text_color(service.data.get("color"), device.color_type)

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_text(
                *client_args, text, text_color=text_color
            ),
        )


async def _send_image_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    image_path = service.data.get("image_path")
    if not image_path:
        raise HomeAssistantError("image_path is required")

    threshold = int(service.data.get("threshold", 128))
    invert = service.data.get("invert", False)

    def _load_image() -> Image.Image:
        return Image.open(image_path)

    image = await hass.async_add_executor_job(_load_image)
    runtime = hass.data[DOMAIN][entry_id]
    device = runtime["data"].device
    if device is None:
        raise HomeAssistantError("Device metadata is not ready yet")

    _ = image_to_draw_bytes(
        image,
        device.columns,
        device.rows,
        threshold=threshold,
        invert=invert,
        color_type=device.color_type,
    )

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda args: send_image(
                args[0],
                args[1],
                args[2],
                args[3],
                image,
                threshold=threshold,
                invert=invert,
            ),
        )


async def _send_animation_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    image_path = service.data.get("image_path")
    if not image_path:
        raise HomeAssistantError("image_path is required")

    speed_ms = service.data.get("speed_ms")
    threshold = int(service.data.get("threshold", 128))
    invert = service.data.get("invert", False)

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_animation(
                *client_args,
                image_path,
                speed_ms=speed_ms,
                threshold=threshold,
                invert=invert,
            ),
        )


async def _send_jt_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    jt_path = service.data.get("jt_path")
    if not jt_path:
        raise HomeAssistantError("jt_path is required")

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_jt(*client_args, jt_path),
        )


async def _set_icon_on_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    icon_id = service.data.get("icon_id")
    if icon_id is None:
        raise HomeAssistantError("icon_id is required")

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: set_icon(*client_args, int(icon_id)),
        )


async def _set_music_on_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    heights = service.data.get("heights")
    colors = service.data.get("colors")
    if not heights or not colors:
        raise HomeAssistantError("heights and colors are required")

    if len(heights) != 8 or len(colors) != 8:
        raise HomeAssistantError("heights and colors must each contain 8 values")

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_music(
                *client_args,
                [int(value) for value in heights],
                [int(value) for value in colors],
            ),
        )


async def _ble_send(hass: HomeAssistant, entry_id: str, sender) -> bool:
    runtime = hass.data[DOMAIN][entry_id]
    address = runtime["address"]
    data: CoolledBluetoothDeviceData = runtime["data"]
    device = data.device
    if device is None:
        raise HomeAssistantError("Device metadata is not ready yet")

    options = _get_options(hass, entry_id)
    ble_device = async_ble_device_from_address(hass, address)
    if ble_device is None:
        raise HomeAssistantError("BLE device is unavailable")

    retries = int(options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT))
    write_delay_ms = int(options.get(CONF_WRITE_DELAY_MS, DEFAULT_WRITE_DELAY_MS))
    password = options.get(CONF_PASSWORD, DEFAULT_PASSWORD)

    for attempt in range(1, retries + 1):
        success = await sender((ble_device, device, password, write_delay_ms))
        if success:
            return True
        _LOGGER.warning(
            "BLE operation failed for %s (attempt %s/%s)",
            address,
            attempt,
            retries,
        )
    raise HomeAssistantError(f"Failed to communicate with {address}")
