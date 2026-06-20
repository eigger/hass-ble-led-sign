"""Config flow for the BLE LED Sign integration."""

from __future__ import annotations

import dataclasses
from typing import Any

import voluptuous as vol

from homeassistant.components import onboarding
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_DRIVER_ID,
    CONF_PASSWORD,
    CONF_RETRY_COUNT,
    CONF_WRITE_DELAY_MS,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_RETRY_COUNT,
    DEFAULT_WRITE_DELAY_MS,
    DOMAIN,
)
from .drivers import BleLedSignBluetoothDeviceData

OPTIONS_SCHEMA = {
    vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): TextSelector(
        TextSelectorConfig(type=TextSelectorType.PASSWORD)
    ),
    vol.Required(CONF_RETRY_COUNT, default=DEFAULT_RETRY_COUNT): NumberSelector(
        NumberSelectorConfig(min=1, max=10, step=1, mode=NumberSelectorMode.BOX)
    ),
    vol.Required(CONF_WRITE_DELAY_MS, default=DEFAULT_WRITE_DELAY_MS): NumberSelector(
        NumberSelectorConfig(
            min=0,
            max=1000,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="ms",
        )
    ),
}


@dataclasses.dataclass
class Discovery:
    """Discovered BLE LED sign device."""

    title: str
    discovery_info: BluetoothServiceInfoBleak
    device: BleLedSignBluetoothDeviceData


def _title(
    discovery_info: BluetoothServiceInfoBleak, device: BleLedSignBluetoothDeviceData
) -> str:
    return (
        device.title
        or device.get_device_name()
        or discovery_info.name
        or DEFAULT_NAME
    )


class BleLedSignConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the BLE LED Sign config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: BleLedSignBluetoothDeviceData | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        device = BleLedSignBluetoothDeviceData()
        if not device.supported(discovery_info):
            return self.async_abort(reason="not_supported")

        device.update(discovery_info)
        title = _title(discovery_info, device)
        self.context["title_placeholders"] = {"name": title}
        self._discovery_info = discovery_info
        self._discovered_device = device
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self._async_get_or_create_entry()
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]
            self.context["title_placeholders"] = {"name": discovery.title}
            self._discovery_info = discovery.discovery_info
            self._discovered_device = discovery.device
            return self._async_get_or_create_entry()

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            device = BleLedSignBluetoothDeviceData()
            if device.supported(discovery_info):
                device.update(discovery_info)
                self._discovered_devices[address] = Discovery(
                    title=_title(discovery_info, device),
                    discovery_info=discovery_info,
                    device=device,
                )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: discovery.title
            for address, discovery in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(titles)}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BleLedSignOptionsFlowHandler()

    def _async_get_or_create_entry(self) -> ConfigFlowResult:
        data: dict[str, Any] = {}
        device = self._discovered_device
        if device is not None and device.driver is not None:
            data[CONF_DRIVER_ID] = device.driver.driver_id
        return self.async_create_entry(
            title=self.context["title_placeholders"]["name"],
            data=data,
        )


class BleLedSignOptionsFlowHandler(OptionsFlowWithReload):
    """BLE LED Sign options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        suggested_values = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(OPTIONS_SCHEMA), suggested_values
            ),
        )
