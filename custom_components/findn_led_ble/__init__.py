"""
Custom integration to integrate findn_led_ble with Home Assistant.

For more details about this integration, please refer to
https://github.com/hirotasoshu/ha-findn-led-ble
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import FindnLedDataUpdateCoordinator
from .data import FindnLedData
from .device import FindnLedDevice

if TYPE_CHECKING:
    from .data import FindnLedConfigEntry

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: FindnLedConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = FindnLedDataUpdateCoordinator(
        hass=hass,
    )
    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(
        hass=hass, address=address.upper(), connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            "Could not find LED BLE device with address %s", address
        )
    device = FindnLedDevice(ble_device)

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Update from a ble callback."""
        device.set_ble_device_and_advertisement_data(
            service_info.device, service_info.advertisement
        )

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            BluetoothCallbackMatcher({ADDRESS: address}),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    entry.runtime_data = FindnLedData(
        title=entry.title,
        device=device,
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def _async_stop(event: Event) -> None:  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
        """Close the connection."""
        await device.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: FindnLedConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        device = entry.runtime_data.device
        await device.stop()
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: FindnLedConfigEntry,
) -> None:
    """Reload config entry."""
    if entry.runtime_data.title != entry.title:
        await hass.config_entries.async_reload(entry.entry_id)  # pyright: ignore[reportUnusedCallResult]
