"""Custom types for findn_led_ble."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import FindnLedDataUpdateCoordinator
    from .device import FindnLedDevice


type FindnLedConfigEntry = ConfigEntry[FindnLedData]


@dataclass
class FindnLedData:
    """Data for the Findn LED BLE integration."""

    title: str
    device: FindnLedDevice
    coordinator: FindnLedDataUpdateCoordinator
