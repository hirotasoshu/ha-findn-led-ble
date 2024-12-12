# pyright: reportImportCycles=false
"""DataUpdateCoordinator for findn_led_ble."""

from __future__ import annotations

from logging import Logger, getLogger
from typing import TYPE_CHECKING, override

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, UPDATE_INTERVAL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import FindnLedConfigEntry

logger: Logger = getLogger(__name__)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class FindnLedDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching data from the device."""

    config_entry: FindnLedConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> None:
        """
        Ensure device connection is established.

        If connection can't be established, exception is raised.
        This will mark device as unavailable.
        """
        await self.config_entry.runtime_data.device.update()
