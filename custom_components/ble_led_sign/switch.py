"""Support for BLE LED sign flip (upside-down) switch entity."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
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
    if not driver_supports(hass, entry.entry_id, "supports_flip"):
        return
    async_add_entities([BleLedSignFlipSwitch(hass, entry)])


class BleLedSignFlipSwitch(RestoreEntity, SwitchEntity):
    """Flip the display upside down."""

    _attr_has_entity_name = True
    _attr_translation_key = "flip"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_flip"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def _set_flip(self, flipped: bool) -> None:
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                "flip",
                1 if flipped else 0,
            ),
        )
        self._attr_is_on = flipped
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_flip(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_flip(False)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"
