"""Connection diagnostics through the real HA entity platform."""

from homeassistant.const import STATE_OFF, STATE_ON

from custom_components.ble_led_sign.const import DOMAIN


async def test_connection_entity_tracks_coordinator(hass, loaded_entry, entity_id):
    """The diagnostic entity follows the session status independently of advertising."""
    connection = entity_id("binary_sensor", "connection")
    assert hass.states.get(connection).state == STATE_OFF
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    runtime["connected"] = True
    runtime["diagnostic_coordinator"].async_set_updated_data(None)
    await hass.async_block_till_done()
    assert hass.states.get(connection).state == STATE_ON
    runtime["connected"] = False
    runtime["diagnostic_coordinator"].async_set_updated_data(None)
    await hass.async_block_till_done()
    assert hass.states.get(connection).state == STATE_OFF
