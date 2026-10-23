"""Support for BLE LED sign speed number entity."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
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
    SPEED_MAX,
    SPEED_MIN,
)
from .device import build_device_info, driver_supports
from .drivers import send_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[NumberEntity] = []
    if driver_supports(hass, entry.entry_id, "supports_speed"):
        entities.append(BleLedSignSpeedNumber(hass, entry))
    if driver_supports(hass, entry.entry_id, "supports_countdown"):
        entities.append(BleLedSignCountdownMinutesNumber(hass, entry))
    async_add_entities(entities)


class BleLedSignCountdownMinutesNumber(RestoreEntity, NumberEntity):
    """Countdown duration in minutes (used by the Start Countdown button)."""

    _attr_has_entity_name = True
    _attr_translation_key = "countdown_minutes"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 99
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_countdown_minutes"
        self._attr_native_value = hass.data[DOMAIN][entry.entry_id]["countdown_minutes"]

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(value)
        self._hass.data[DOMAIN][self._entry_id]["countdown_minutes"] = minutes
        self._attr_native_value = minutes
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        try:
            minutes = int(float(last_state.state))
        except (TypeError, ValueError):
            return
        self._attr_native_value = minutes
        self._hass.data[DOMAIN][self._entry_id]["countdown_minutes"] = minutes


class BleLedSignSpeedNumber(RestoreEntity, NumberEntity):
    """Scroll speed control."""

    _attr_has_entity_name = True
    _attr_translation_key = "speed"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = SPEED_MIN
    _attr_native_max_value = SPEED_MAX
    _attr_native_step = 1

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_speed"
        self._attr_native_value = 50

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_set_native_value(self, value: float) -> None:
        speed = int(value)
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                "speed",
                speed,
            ),
        )
        self._attr_native_value = speed
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        try:
            self._attr_native_value = float(last_state.state)
        except (TypeError, ValueError):
            pass
