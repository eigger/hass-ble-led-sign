"""Support for BLE LED sign clear-display button entity."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from propcache.api import cached_property

from .ble import async_send
from .const import (
    DOMAIN,
)
from .device import build_device_info, driver_supports
from .drivers import send_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[ButtonEntity] = []
    if driver_supports(hass, entry.entry_id, "supports_clear"):
        entities.append(BleLedSignClearButton(hass, entry))
    if driver_supports(hass, entry.entry_id, "supports_countdown"):
        entities.append(BleLedSignStartCountdownButton(hass, entry))
    async_add_entities(entities)


class BleLedSignClearButton(ButtonEntity):
    """Clear all content stored on the display."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_clear"

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                "clear",
            ),
        )


class BleLedSignStartCountdownButton(ButtonEntity):
    """Start the countdown timer using the Countdown Minutes value."""

    _attr_has_entity_name = True
    _attr_translation_key = "start_countdown"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_start_countdown"

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        runtime = self._hass.data[DOMAIN][self._entry_id]
        minutes = int(runtime.get("countdown_minutes", 5))
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                "countdown",
                [1, minutes, 0],
            ),
        )
