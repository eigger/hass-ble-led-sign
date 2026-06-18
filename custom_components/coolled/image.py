"""Support for CoolLED label preview and last-sent image."""

from __future__ import annotations

import logging

from homeassistant.components.image import Image, ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from propcache.api import cached_property

from .const import DOMAIN
from .device import build_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    image_coordinator = hass.data[DOMAIN][entry.entry_id]["image_coordinator"]
    preview_coordinator = hass.data[DOMAIN][entry.entry_id]["preview_coordinator"]
    async_add_entities(
        [
            CoolledImageEntity(hass, entry, image_coordinator),
            CoolledPreviewImageEntity(hass, entry, preview_coordinator),
        ]
    )


class CoolledImageEntity(CoordinatorEntity[DataUpdateCoordinator[bytes | None]], ImageEntity):
    """Last image successfully sent to the device."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_updated_content"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator[bytes | None],
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"coolled_{self._identifier}_last_updated_content"
        self._attr_content_type = "image/png"
        self._cached_image = Image(content_type="image/png", content=coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    def image(self) -> bytes | None:
        return self._cached_image.content if self._cached_image else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._cached_image = Image(content_type="image/png", content=self.coordinator.data)
        self._attr_image_last_updated = dt_util.now()
        super()._handle_coordinator_update()


class CoolledPreviewImageEntity(
    CoordinatorEntity[DataUpdateCoordinator[bytes | None]], ImageEntity
):
    """Preview of the most recently rendered label."""

    _attr_has_entity_name = True
    _attr_translation_key = "preview_content"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator[bytes | None],
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        address = hass.data[DOMAIN][entry.entry_id]["address"]
        self._address = address
        self._identifier = address.replace(":", "")[-8:].upper()
        self._attr_unique_id = f"coolled_{self._identifier}_preview_content"
        self._attr_content_type = "image/png"
        self._cached_image = Image(content_type="image/png", content=coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        return build_device_info(self._address)

    @cached_property
    def available(self) -> bool:
        return True

    def image(self) -> bytes | None:
        return self._cached_image.content if self._cached_image else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._cached_image = Image(content_type="image/png", content=self.coordinator.data)
        self._attr_image_last_updated = dt_util.now()
        super()._handle_coordinator_update()
