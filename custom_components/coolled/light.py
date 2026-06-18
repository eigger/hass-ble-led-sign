"""Support for CoolLED light entity."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from propcache.api import cached_property

from .device import build_device_info
from .const import (
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    BRIGHTNESS_OFFSET,
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
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
    async_add_entities([CoolledLight(hass, entry)])


class CoolledLight(RestoreEntity, LightEntity):
    """CoolLED sign as a light entity (power + brightness)."""

    _attr_has_entity_name = True
    _attr_translation_key = "display"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(MODES_1248.values())

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._hass = hass
        self._entry_id = entry.entry_id
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"coolled_{self._identifier}_display"
        self._attr_is_on = True
        self._attr_brightness = 128
        self._attr_effect = MODES_1248[1]

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    async def _send(self, command: str, value: int | None = None) -> None:
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
            success = await send_command(
                ble_device,
                device,
                password,
                write_delay_ms,
                command,
                value,
            )
            if success:
                return
            _LOGGER.warning(
                "Command %s failed for %s (attempt %s/%s)",
                command,
                self._address,
                attempt,
                retries,
            )
        raise HomeAssistantError(f"Failed to send {command} to {self._address}")

    async def async_turn_on(self, **kwargs) -> None:
        brightness = kwargs.get("brightness")
        effect = kwargs.get("effect")

        if brightness is not None:
            self._attr_brightness = brightness
            await self._send("brightness", brightness + BRIGHTNESS_OFFSET)
        if effect is not None and effect in self._attr_effect_list:
            self._attr_effect = effect
            mode = next(k for k, v in MODES_1248.items() if v == effect)
            await self._send("mode", mode)
        await self._send("turn_on")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self._send("turn_off")
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state:
            self._attr_is_on = last_state.state == "on"
        if (brightness := last_state.attributes.get("brightness")) is not None:
            self._attr_brightness = max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, brightness))
        if (effect := last_state.attributes.get("effect")) in self._attr_effect_list:
            self._attr_effect = effect
