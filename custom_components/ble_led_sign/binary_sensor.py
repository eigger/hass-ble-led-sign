"""Actual GATT connection state, separate from advertisement availability."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import build_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a connection diagnostic."""
    async_add_entities([BleConnectionSensor(hass, entry)])


class BleConnectionSensor(CoordinatorEntity, BinarySensorEntity):
    """On only while this integration holds an active BLE session."""

    _attr_has_entity_name = True
    _attr_translation_key = "connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, hass, entry):
        self.runtime = hass.data[DOMAIN][entry.entry_id]
        super().__init__(self.runtime["diagnostic_coordinator"])
        self._attr_unique_id = f"{entry.unique_id}_connection"
        self._attr_device_info = build_device_info(entry.unique_id)

    @property
    def is_on(self):
        return self.runtime["connected"]
