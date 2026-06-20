"""The BLE LED Sign Bluetooth integration."""

from __future__ import annotations

import logging
from asyncio import Lock
from functools import partial
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
    async_last_service_info,
)
from homeassistant.const import ATTR_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from PIL import Image, ImageColor

from .const import (
    CONF_DRIVER_ID,
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
    LOCK,
    MANUFACTURER,
)
from .coordinator import BleLedSignPassiveBluetoothProcessorCoordinator
from .device import sync_device_registry
from .drivers import (
    BleLedSignBluetoothDeviceData,
    get_driver,
    send_animation,
    send_command,
    send_image,
    send_jt,
    send_music,
    send_text,
    set_icon,
)
from .drivers.coolled.text import (
    image_file_to_png_bytes,
    image_to_draw_bytes,
    resolve_text_color,
)
from .renderer import render_image
from .services import SERVICE_NAMES
from .types import BleLedSignConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
]

_LOGGER = logging.getLogger(__name__)


def process_service_info(
    hass: HomeAssistant,
    entry: BleLedSignConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Update device metadata from BLE advertisements."""
    entry.runtime_data.device_data.update(service_info)
    sync_device_registry(hass, entry, service_info)

    # For families whose size/colour isn't advertised, query it once over a
    # connection as soon as the device is seen (in case it wasn't reachable at
    # setup time).
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not runtime:
        return
    driver = runtime.get("driver")
    device = runtime["data"].device
    if (
        driver is not None
        and getattr(driver, "requires_active_info", False)
        and device is not None
        and not device.columns
        and not runtime.get("info_fetching")
    ):
        runtime["info_fetching"] = True
        entry.async_create_background_task(
            hass, _async_fetch_device_info(hass, entry), f"{DOMAIN}_fetch_info"
        )


def _resolve_driver(
    entry: BleLedSignConfigEntry, data: BleLedSignBluetoothDeviceData
):
    """Resolve the driver for an entry from stored id or live advertisement."""
    driver_id = entry.data.get(CONF_DRIVER_ID)
    if not driver_id and data.device is not None:
        driver_id = data.device.driver_id
    if not driver_id:
        return None
    try:
        return get_driver(driver_id)
    except KeyError:
        _LOGGER.warning("Unknown driver id %r for entry %s", driver_id, entry.entry_id)
        return None


async def async_setup_entry(hass: HomeAssistant, entry: BleLedSignConfigEntry) -> bool:
    """Set up a BLE LED sign from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if LOCK not in hass.data[DOMAIN]:
        hass.data[DOMAIN][LOCK] = Lock()

    address = entry.unique_id
    assert address is not None

    data = BleLedSignBluetoothDeviceData()
    # Seed device metadata from the latest advertisement so capability-gated
    # platforms know which driver to use before the coordinator starts.
    service_info = async_last_service_info(hass, address, connectable=True)
    if service_info is not None:
        data.update(service_info)

    driver = _resolve_driver(entry, data)

    hass.data[DOMAIN][entry.entry_id] = {
        "address": address,
        "data": data,
        "driver": driver,
        "image_coordinator": DataUpdateCoordinator(hass, _LOGGER, name=f"{DOMAIN}_image"),
        "preview_coordinator": DataUpdateCoordinator(hass, _LOGGER, name=f"{DOMAIN}_preview"),
    }

    device_registry = dr.async_get(hass)
    identifier = address.replace(":", "")[-8:].upper()
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(CONNECTION_BLUETOOTH, address)},
        manufacturer=MANUFACTURER,
        name=f"{DEFAULT_NAME} {identifier}",
    )
    hass.data[DOMAIN][entry.entry_id]["device_id"] = device_entry.id

    bt_coordinator = BleLedSignPassiveBluetoothProcessorCoordinator(
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

    async def send_command_service(service: ServiceCall) -> None:
        await _run_for_devices(hass, service, _send_command_to_device)

    for service_name in SERVICE_NAMES:
        handler = {
            "write": write_service,
            "send_text": send_text_service,
            "send_image": send_image_service,
            "send_animation": send_animation_service,
            "send_jt": send_jt_service,
            "set_icon": set_icon_service,
            "set_music": set_music_service,
            "send_command": send_command_service,
        }[service_name]
        hass.services.async_register(DOMAIN, service_name, handler)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(bt_coordinator.async_start())

    # Some families (e.g. iPixel Color) don't advertise their panel size; read
    # it over a connection in the background and refresh the device registry.
    if driver is not None and getattr(driver, "requires_active_info", False):
        hass.data[DOMAIN][entry.entry_id]["info_fetching"] = True
        entry.async_create_background_task(
            hass, _async_fetch_device_info(hass, entry), f"{DOMAIN}_fetch_info"
        )

    return True


async def _async_fetch_device_info(
    hass: HomeAssistant, entry: BleLedSignConfigEntry
) -> None:
    """Read panel metadata over a connection and update the device registry."""
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not runtime:
        return
    driver = runtime.get("driver")
    data: BleLedSignBluetoothDeviceData = runtime["data"]
    try:
        if driver is None or data.device is None:
            return
        ble_device = async_ble_device_from_address(hass, runtime["address"])
        if ble_device is None:
            return
        async with hass.data[DOMAIN][LOCK]:
            ok = await driver.async_fetch_info(ble_device, data.device)
        if ok and data.last_service_info is not None:
            sync_device_registry(hass, entry, data.last_service_info)
    finally:
        # Allow a later advertisement to retry if the size is still unknown.
        runtime["info_fetching"] = False


async def async_unload_entry(hass: HomeAssistant, entry: BleLedSignConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if unload_ok and len(hass.config_entries.async_entries(DOMAIN)) == 0:
        for service in SERVICE_NAMES:
            hass.services.async_remove(DOMAIN, service)
    return unload_ok


def _normalize_device_ids(service: ServiceCall) -> list[str]:
    # Home Assistant merges the service ``target`` (device_id/entity_id/area_id)
    # into ``service.data``; ServiceCall has no ``target`` attribute.
    device_ids = service.data.get(ATTR_DEVICE_ID)
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
    raise HomeAssistantError(
        f"No BLE LED Sign entry found for device_id {device_id!r}"
    )


def _get_options(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    entry = hass.config_entries.async_get_entry(entry_id)
    return {**(entry.data if entry else {}), **(entry.options if entry else {})}


async def _render_label(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> tuple[Image.Image, bytes]:
    runtime = hass.data[DOMAIN][entry_id]
    data: BleLedSignBluetoothDeviceData = runtime["data"]
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
    if device.columns and device.rows:
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


def _parse_rgb(value: str | None) -> tuple[int, int, int] | None:
    """Parse a hex/named color into an RGB tuple, or None."""
    if not value:
        return None
    try:
        rgb = ImageColor.getrgb(value if str(value).startswith("#") else f"#{value}")
    except ValueError:
        try:
            rgb = ImageColor.getrgb(str(value))
        except ValueError:
            return None
    return (rgb[0], rgb[1], rgb[2])


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

    driver = runtime.get("driver")
    raw_color = service.data.get("color")
    # Full-color drivers take a true RGB color; CoolLED snaps to its palette.
    if driver is not None and getattr(driver, "driver_id", "") == "ipixel_color":
        text_color = _parse_rgb(raw_color) or (255, 255, 255)
    else:
        text_color = resolve_text_color(raw_color, device.color_type)

    options: dict[str, Any] = {}
    for key in ("animation", "speed", "rainbow", "save_slot"):
        if service.data.get(key) is not None:
            options[key] = int(service.data[key])
    if (bg := _parse_rgb(service.data.get("bg_color"))) is not None:
        options["bg_color"] = bg
    if service.data.get("font"):
        options["font_path"] = service.data["font"]

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_text(
                *client_args, text, text_color=text_color, **options
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

    if device.columns and device.rows:
        _ = image_to_draw_bytes(
            image,
            device.columns,
            device.rows,
            threshold=threshold,
            invert=invert,
            color_type=device.color_type,
        )

    save_slot = int(service.data.get("save_slot", 0))

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
                save_slot=save_slot,
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
    save_slot = int(service.data.get("save_slot", 0))

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
                save_slot=save_slot,
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


async def _send_command_to_device(
    hass: HomeAssistant, entry_id: str, service: ServiceCall
) -> None:
    command = service.data.get("command")
    if not command:
        raise HomeAssistantError("command is required")
    value = service.data.get("value")

    async with hass.data[DOMAIN][LOCK]:
        await _ble_send(
            hass,
            entry_id,
            lambda client_args: send_command(*client_args, command, value),
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
    data: BleLedSignBluetoothDeviceData = runtime["data"]
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
