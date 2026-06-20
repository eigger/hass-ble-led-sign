"""Support for BLE LED sign display text entity."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.text import RestoreText
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from propcache.api import cached_property

from .device import build_device_info, driver_supports
from .const import (
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
)
from .drivers import send_text

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if not driver_supports(hass, entry.entry_id, "supports_text"):
        return
    async_add_entities([BleLedSignDisplayText(hass, entry)])


class BleLedSignDisplayText(RestoreText):
    """Text shown on the BLE LED sign."""

    _attr_has_entity_name = True
    _attr_translation_key = "display_text"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_max = 128
    _attr_native_min = 0
    _attr_mode = "text"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_display_text"
        self._attr_native_value = "Hello"

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_set_value(self, value: str) -> None:
        entry = self._hass.config_entries.async_get_entry(self._entry_id)
        options = {**(entry.data if entry else {}), **(entry.options if entry else {})}
        data = self._hass.data[DOMAIN][self._entry_id]["data"]
        device = data.device
        if device is None:
            raise HomeAssistantError("Device metadata is not ready yet")

        ble_device = async_ble_device_from_address(self._hass, self._address)
        if ble_device is None:
            raise HomeAssistantError("BLE device is unavailable")

        retries = int(options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT))
        write_delay_ms = int(options.get(CONF_WRITE_DELAY_MS, DEFAULT_WRITE_DELAY_MS))
        password = options.get(CONF_PASSWORD, DEFAULT_PASSWORD)

        for attempt in range(1, retries + 1):
            success = await send_text(
                ble_device, device, password, write_delay_ms, value
            )
            if success:
                self._attr_native_value = value
                self.async_write_ha_state()
                return
            _LOGGER.warning(
                "Text send failed for %s (attempt %s/%s)",
                self._address,
                attempt,
                retries,
            )
        raise HomeAssistantError("Failed to send text")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_text_data := await self.async_get_last_text_data()) is None:
            return
        self._attr_native_value = last_text_data.native_value
