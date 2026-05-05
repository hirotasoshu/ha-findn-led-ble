"""BLE transport for Findn LED devices."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from bleak.exc import BleakDBusError, BleakError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
    retry_bluetooth_connection_error,
)

from .const import WRITE_CHARACTERISTIC_UUID

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Lock

    from bleak.backends.characteristic import BleakGATTCharacteristic
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    from bleak.backends.service import BleakGATTServiceCollection

BLEAK_BACKOFF_TIME = 0.25
COMMAND_SETTLE_DELAY = 0.1
DEFAULT_ATTEMPTS = 3
DISCONNECT_DELAY = 120

logger = logging.getLogger(__name__)


class CharacteristicMissingError(Exception):
    """Raised when a characteristic is missing."""


class FindnLedBleTransport:
    """Manage BLE connection lifecycle and command writes."""

    def __init__(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData | None = None
    ) -> None:
        """Initialize the BLE transport."""
        self._ble_device: BLEDevice = ble_device
        self._advertisement_data: AdvertisementData | None = advertisement_data
        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._expected_disconnect: bool = False
        self._operation_lock: Lock = asyncio.Lock()
        self._write_char: BleakGATTCharacteristic | None = None
        self.loop: AbstractEventLoop = asyncio.get_running_loop()

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Update the BLE device and advertisement data from discovery."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data

    @property
    def address(self) -> str:
        """Return the BLE address."""
        return self._ble_device.address

    @property
    def name(self) -> str:
        """Return the BLE device name."""
        return self._ble_device.name or self._ble_device.address

    @property
    def rssi(self) -> int | None:
        """Return the latest RSSI from advertisement data."""
        if self._advertisement_data:
            return self._advertisement_data.rssi
        return None

    async def connect(self) -> None:
        """Ensure the BLE connection is established."""
        if self._connect_lock.locked():
            logger.debug(
                "%s: Connection already in progress, waiting for it to complete; "
                "RSSI: %s",
                self.name,
                self.rssi,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return
        async with self._connect_lock:
            if self._client and self._client.is_connected:
                self._reset_disconnect_timer()
                return
            logger.debug("%s: Connecting; RSSI: %s", self.name, self.rssi)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._ble_device,
            )
            logger.debug("%s: Connected; RSSI: %s", self.name, self.rssi)

            if not self._resolve_characteristics(client.services):
                await self._handle_missing_characteristic(client)
                raise CharacteristicMissingError("Write characteristic missing")

            self._client = client
            self._reset_disconnect_timer()

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        self._cancel_disconnect_timer()
        await self._execute_disconnect()

    async def write_commands(self, commands: list[bytes] | bytes) -> None:
        """Write one or more commands to the connected BLE device."""
        await self.connect()
        if not isinstance(commands, list):
            commands = [commands]
        logger.debug(
            "%s: Sending commands %s",
            self.name,
            [command.hex() for command in commands],
        )
        if self._operation_lock.locked():
            logger.debug(
                "%s: Operation already in progress, waiting for it to complete; "
                "RSSI: %s",
                self.name,
                self.rssi,
            )
        async with self._operation_lock:
            try:
                await self._write_commands_locked(commands)
            except BleakNotFoundError:
                logger.exception(
                    "%s: device not found, no longer in range, or poor RSSI: %s",
                    self.name,
                    self.rssi,
                )
                raise
            except CharacteristicMissingError:
                logger.exception(
                    "%s: write characteristic missing; RSSI: %s",
                    self.name,
                    self.rssi,
                )
                raise
            except BLEAK_EXCEPTIONS:
                logger.exception("%s: communication failed", self.name)
                raise

    def _cancel_disconnect_timer(self) -> None:
        """Cancel the idle disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:  # noqa: ARG002 # pyright: ignore[reportUnusedParameter]
        """Handle BLE disconnection notifications."""
        if self._expected_disconnect:
            logger.debug("%s: Disconnected from device; RSSI: %s", self.name, self.rssi)
            return
        logger.warning(
            "%s: Device unexpectedly disconnected; RSSI: %s",
            self.name,
            self.rssi,
        )
        self._cancel_disconnect_timer()

    def _disconnect(self) -> None:
        """Schedule an idle BLE disconnect."""
        self._disconnect_timer = None
        asyncio.create_task(self._execute_timed_disconnect())  # noqa: RUF006

    async def _execute_disconnect(self) -> None:
        """Disconnect while holding the connection lock."""
        async with self._connect_lock:
            client = self._client
            self._expected_disconnect = True
            self._client = None
            self._write_char = None
            if client and client.is_connected:
                await client.disconnect()

    async def _execute_timed_disconnect(self) -> None:
        """Disconnect after the idle timeout expires."""
        logger.debug(
            "%s: Disconnecting after timeout of %s",
            self.name,
            DISCONNECT_DELAY,
        )
        await self._execute_disconnect()

    async def _handle_missing_characteristic(
        self, client: BleakClientWithServiceCache
    ) -> None:
        """Clear stale service cache after a missing characteristic."""
        logger.debug("%s: write characteristic missing, clearing cache", self.name)
        await client.clear_cache()
        self._expected_disconnect = True
        if client.is_connected:
            await client.disconnect()
        self._write_char = None

    async def _execute_commands_locked(self, commands: list[bytes]) -> None:
        """Execute command writes while the operation lock is held."""
        assert self._client is not None  # noqa: S101
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")
        for command in commands:
            await self._client.write_gatt_char(
                self._write_char, command, response=False
            )
            await asyncio.sleep(COMMAND_SETTLE_DELAY)

    def _reset_disconnect_timer(self) -> None:
        """Reset the idle disconnect timer."""
        self._cancel_disconnect_timer()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            DISCONNECT_DELAY, self._disconnect
        )

    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> bool:
        """Resolve the BLE write characteristic."""
        self._write_char = services.get_characteristic(WRITE_CHARACTERISTIC_UUID)
        return bool(self._write_char)

    @retry_bluetooth_connection_error(DEFAULT_ATTEMPTS)
    async def _write_commands_locked(self, commands: list[bytes]) -> None:
        """Write commands with bluetooth retry handling."""
        try:
            await self._execute_commands_locked(commands)
        except BleakDBusError as ex:
            await asyncio.sleep(BLEAK_BACKOFF_TIME)
            logger.debug(
                "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                self.name,
                self.rssi,
                BLEAK_BACKOFF_TIME,
                ex,
            )
            await self._execute_disconnect()
            raise
        except BleakError as ex:
            logger.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s",
                self.name,
                self.rssi,
                ex,
            )
            await self._execute_disconnect()
            raise
