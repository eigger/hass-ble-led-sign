"""Support for CoolLED scroll mode select entity."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from propcache.api import cached_property

from .device import build_device_info
from .const import (
    CONF_PASSWORD,
    CONF_WRITE_DELAY_MS,
    DEFAULT_PASSWORD,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
    MODES_1248,
)
from .coolled_ble import send_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([CoolledModeSelect(hass, entry)])


class CoolledModeSelect(RestoreEntity, SelectEntity):
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
        self._attr_unique_id = f"coolled_{self._identifier}_mode"
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
        entry = self._hass.config_entries.async_get_entry(self._entry_id)
        options = {**(entry.data if entry else {}), **(entry.options if entry else {})}
        data = self._hass.data[DOMAIN][self._entry_id]["data"]
        device = data.device
        if device is None:
            raise HomeAssistantError("Device metadata is not ready yet")

        ble_device = async_ble_device_from_address(self._hass, self._address)
        if ble_device is None:
            raise HomeAssistantError("BLE device is unavailable")

        success = await send_command(
            ble_device,
            device,
            options.get(CONF_PASSWORD, DEFAULT_PASSWORD),
            int(options.get(CONF_WRITE_DELAY_MS, DEFAULT_WRITE_DELAY_MS)),
            "mode",
            mode,
        )
        if not success:
            raise HomeAssistantError("Failed to set mode")
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state in self._attr_options:
            self._attr_current_option = last_state.state
