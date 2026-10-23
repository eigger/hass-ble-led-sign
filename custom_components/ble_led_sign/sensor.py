"""Diagnostic readings for completed BLE sessions."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import build_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Expose reports even when a sign is unreachable."""
    async_add_entities(
        [
            BleSessionSensor(hass, entry, key)
            for key in ("last_operation", "last_error", "last_failure", "failure_count")
        ]
    )


class BleSessionSensor(CoordinatorEntity, SensorEntity):
    """A diagnostic that survives a failed write and subsequent recovery."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass, entry, key):
        self.runtime = hass.data[DOMAIN][entry.entry_id]
        super().__init__(self.runtime["diagnostic_coordinator"])
        self.key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = build_device_info(entry.unique_id)
        if key == "last_failure":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Keep states short; the report belongs in attributes."""
        reports = self.runtime["reports"]
        if self.key == "failure_count":
            return reports.failures
        if self.key == "last_failure":
            return reports.last_failure_at
        if self.key == "last_error":
            return (
                reports.last_failure.get("failed_stage", "unknown")
                if reports.last_failure
                else "none"
            )
        if reports.last is None:
            return None
        return "success" if reports.last["success"] else "failed"

    @property
    def extra_state_attributes(self):
        reports = self.runtime["reports"]
        report = reports.last if self.key == "last_operation" else reports.last_failure
        return dict(report) if report else {}
