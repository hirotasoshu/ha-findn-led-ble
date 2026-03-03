"""FindnLedEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FindnLedDataUpdateCoordinator


class FindnLedEntity(CoordinatorEntity[FindnLedDataUpdateCoordinator]):
    """BlueprintEntity class."""

    def __init__(self, coordinator: FindnLedDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id: str | None = coordinator.config_entry.entry_id
        self._attr_device_info: DeviceInfo | None = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )
