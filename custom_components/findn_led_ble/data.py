"""Custom types for findn_led_ble."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from custom_components.findn_led_ble.device import FindnLedDevice


type FindnLedConfigEntry = ConfigEntry[FindnLedData]


@dataclass
class FindnLedData:
    """Data for the Findn LED BLE integration."""

    title: str
    device: FindnLedDevice
