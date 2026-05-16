"""FindnLedEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

if TYPE_CHECKING:
    from custom_components.findn_led_ble.data import FindnLedConfigEntry
    from custom_components.findn_led_ble.device import FindnLedDevice


class FindnLedEntity(Entity):
    """Base entity for Findn LED BLE."""

    _attr_has_entity_name = True

    def __init__(self, entry: FindnLedConfigEntry, device: FindnLedDevice) -> None:
        """Initialize."""
        self.device = device
        self._attr_unique_id: str | None = device.address
        self._attr_device_info: dr.DeviceInfo | None = dr.DeviceInfo(
            name=device.name,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
            identifiers={(entry.domain, entry.entry_id)},
        )
