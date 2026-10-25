"""Session result sensors on actual loaded HA platforms."""

from custom_components.ble_led_sign.const import DOMAIN


async def test_operation_report_after_real_service(hass, loaded_entry, entity_id):
    """A completed external-boundary-mocked send publishes its session report."""
    count = entity_id("sensor", "failure_count")
    assert hass.states.get(count).state == "0"
    device_id = hass.data[DOMAIN][loaded_entry.entry_id]["device_id"]
    await hass.services.async_call(
        DOMAIN, "send_text", {"device_id": device_id, "text": "HA"}, blocking=True
    )
    await hass.async_block_till_done()
    result = hass.states.get(entity_id("sensor", "last_operation"))
    assert result.state == "success"
    assert result.attributes["success"] is True
    assert hass.states.get(entity_id("sensor", "last_error")).state == "none"
