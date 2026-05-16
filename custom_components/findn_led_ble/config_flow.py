"""Adds config flow for Blueprint."""

from __future__ import annotations

from logging import Logger, getLogger
from typing import Any, Final, override

import voluptuous as vol
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS
from bluetooth_data_tools import human_readable_name
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from custom_components.findn_led_ble.const import DOMAIN, LOCAL_NAME
from custom_components.findn_led_ble.device import FindnLedDevice

logger: Logger = getLogger(__name__)


class FindnLedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yale Access Bluetooth."""

    VERSION: Final[int] = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    @override
    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        return await self.async_step_user()

    @override
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = str(user_input[CONF_ADDRESS])  # pyright: ignore[reportAny]
            discovery_info = self._discovered_devices[address]
            errors = await self._async_validate_discovery(discovery_info)
            if not errors:
                return self.async_create_entry(
                    title=discovery_info.name,
                    data={
                        CONF_ADDRESS: discovery_info.address,
                    },
                )

        self._async_populate_discovered_devices()

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: (
                            f"{service_info.name} ({service_info.address})"
                        )
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def _async_validate_discovery(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> dict[str, str]:
        """Validate that a discovered device can be contacted."""
        await self.async_set_unique_id(discovery_info.address, raise_on_progress=False)
        self._abort_if_unique_id_configured()
        device = FindnLedDevice(discovery_info.device)
        try:
            await device.identify()
        except BLEAK_EXCEPTIONS:
            return {"base": "cannot_connect"}
        except Exception:
            logger.exception("Unexpected error")
            return {"base": "unknown"}
        finally:
            await device.stop()
        return {}

    def _async_populate_discovered_devices(self) -> None:
        """Populate flow choices from current discovery data."""
        discovery = self._discovery_info
        if discovery:
            self._discovered_devices[discovery.address] = discovery
            return

        current_addresses = {
            address for address in self._async_current_ids() if address is not None
        }
        for discovery in async_discovered_service_info(self.hass):
            if self._async_should_skip_discovery(discovery, current_addresses):
                continue
            self._discovered_devices[discovery.address] = discovery

    def _async_should_skip_discovery(
        self,
        discovery: BluetoothServiceInfoBleak,
        current_addresses: set[str],
    ) -> bool:
        """Return whether a discovered device should be skipped."""
        return (
            discovery.address in current_addresses
            or discovery.address in self._discovered_devices
            or not discovery.name.startswith(LOCAL_NAME)
        )
