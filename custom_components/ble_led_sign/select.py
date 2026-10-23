"""Support for BLE LED sign scroll mode select entity."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from propcache.api import cached_property

from .ble import async_send
from .const import (
    DOMAIN,
    MODES_1248,
)
from .device import build_device_info, driver_supports, get_entry_driver
from .drivers import send_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SelectEntity] = []
    if driver_supports(hass, entry.entry_id, "supports_mode"):
        entities.append(BleLedSignModeSelect(hass, entry))
    driver = get_entry_driver(hass, entry.entry_id)
    if driver is not None and driver.display_modes:
        entities.append(BleLedSignDisplayModeSelect(hass, entry))
    async_add_entities(entities)


class BleLedSignModeSelect(RestoreEntity, SelectEntity):
    """Scroll mode selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "mode"
    _attr_options = list(MODES_1248.values())

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_mode"
        self._attr_current_option = MODES_1248[1]

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise HomeAssistantError(f"Unknown mode: {option}")

        mode = next(key for key, value in MODES_1248.items() if value == option)
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                "mode",
                mode,
            ),
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state in self._attr_options:
            self._attr_current_option = last_state.state


class BleLedSignDisplayModeSelect(RestoreEntity, SelectEntity):
    """Built-in display mode selector (clock, stopwatch, scoreboard, …)."""

    _attr_has_entity_name = True
    _attr_translation_key = "display_mode"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"ble_led_sign_{self._identifier}_display_mode"
        driver = get_entry_driver(hass, entry.entry_id)
        self._modes = dict(driver.display_modes) if driver else {}
        self._attr_options = list(self._modes)
        self._attr_current_option = (
            self._attr_options[0] if self._attr_options else None
        )

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def async_select_option(self, option: str) -> None:
        if option not in self._modes:
            raise HomeAssistantError(f"Unknown display mode: {option}")

        command, value = self._modes[option]
        await async_send(
            self._hass,
            self._entry_id,
            lambda args: send_command(
                *args,
                command,
                value,
            ),
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state in self._attr_options:
            self._attr_current_option = last_state.state
