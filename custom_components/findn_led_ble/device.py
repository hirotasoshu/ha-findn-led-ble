"""Findn LED BLE Device."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from bleak.exc import BleakDBusError, BleakError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
    retry_bluetooth_connection_error,
)

from .const import (
    WRITE_CHARACTERISTIC_UUID,
)
from .device_protocol import FindnLedBLEProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from bleak.backends.characteristic import BleakGATTCharacteristic
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData
    from bleak.backends.service import BleakGATTServiceCollection

BLEAK_BACKOFF_TIME = 0.25

DISCONNECT_DELAY = 120

RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError,)

logger = logging.getLogger(__name__)

DEFAULT_ATTEMPTS = 3


class CharacteristicMissingError(Exception):
    """Raised when a characteristic is missing."""


@dataclass(frozen=True)
class FindnLedState:
    """Findn LED state."""

    power: bool = False
    hs: tuple[float, float] = (0, 0)
    brightness: int = 1
    effect: int = None


class FindnLedDevice:
    """Findn LED BLE Device."""

    def __init__(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData | None = None
    ) -> None:
        """Init the Findn LED BLE."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._operation_lock = asyncio.Lock()
        self._state = FindnLedState()
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._write_char: BleakGATTCharacteristic | None = None
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._client: BleakClientWithServiceCache | None = None
        self._expected_disconnect = False
        self.loop = asyncio.get_running_loop()
        self._update_callback: Callable[[], None] | None = None
        self._protocol: FindnLedBLEProtocol = FindnLedBLEProtocol()

    def update_callback(self) -> None:
        """Execute update callback if set."""
        if self._update_callback:
            self._update_callback()

    def set_update_callback(self, callback: Callable[[], None]) -> None:
        """Set the update callback."""
        self._update_callback = callback

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Set the ble device."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data

    @property
    def address(self) -> str:
        """Return the address."""
        return self._ble_device.address

    @property
    def _address(self) -> str:
        """Return the address."""
        return self._ble_device.address

    @property
    def name(self) -> str:
        """Get the name of the device."""
        return self._ble_device.name or self._ble_device.address

    @property
    def rssi(self) -> int | None:
        """Get the rssi of the device."""
        if self._advertisement_data:
            return self._advertisement_data.rssi
        return None

    @property
    def state(self) -> FindnLedState:
        """Return the state."""
        return self._state

    @property
    def hs(self) -> tuple[float, float]:
        """Return current color in HS."""
        return self._state.hs

    @property
    def is_on(self) -> bool:
        """Return device is on/off."""
        return self._state.power

    @property
    def brightness(self) -> int:
        """Return current brightness 0-255."""
        return self._state.brightness

    @property
    def effect(self) -> int:
        """Return current effect."""
        return self._state.effect

    async def update(self) -> None:
        """Update the Findn LED BLE."""
        await self._ensure_connected()
        logger.debug("%s: Updating", self.name)

    async def turn_on(self) -> None:
        """Turn on."""
        logger.debug("%s: Turn on", self.name)
        await self._send_command(self._protocol.turn_on_command)
        self._state = replace(self._state, power=True)
        self.update_callback()

    async def turn_off(self) -> None:
        """Turn off."""
        logger.debug("%s: Turn off", self.name)
        await self._send_command(self._protocol.turn_off_command)
        self._state = replace(self._state, power=False)
        self.update_callback()

    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness."""
        logger.debug("%s: Set brightness: %s", self.name, brightness)
        await self._send_command(
            self._protocol.construct_set_brightness_cmd(brightness)
        )
        self._state = replace(self._state, brightness=brightness)
        self.update_callback()

    async def set_hs_color(self, hs: tuple[float, float]) -> None:
        """Set color using hue and saturation."""
        logger.debug("%s: Set hs color: %s", self.name, hs)
        await self._send_command(self._protocol.construct_set_hs_color_cmd(hs))
        self._state = replace(self._state, hs=hs)
        self.update_callback()

    async def set_effect(self, effect: int) -> None:
        """Set the effect effect."""
        logger.debug("%s: Set effect: %s", self.name, effect)
        await self._send_command(
            self._protocol.construct_set_effect_cmd(effect)
        )
        self._state = replace(self._state, effect=effect)
        self.update_callback()

    async def stop(self) -> None:
        """Stop the Findn LED BLE."""
        logger.debug("%s: Stop", self.name)
        await self._execute_disconnect()

    async def _ensure_connected(self) -> None:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            logger.debug(
                "%s: Connection already in progress, waiting for it to complete; RSSI: %s",  # noqa: E501
                self.name,
                self.rssi,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return
        async with self._connect_lock:
            # Check again while holding the lock
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
            resolved = self._resolve_characteristics(client.services)
            if not resolved:
                # Try to handle services failing to load
                resolved = self._resolve_characteristics(await client.get_services())  # pyright: ignore[reportUnknownMemberType]

            self._client = client
            self._reset_disconnect_timer()

    def _reset_disconnect_timer(self) -> None:
        """Reset disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            DISCONNECT_DELAY, self._disconnect
        )

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:  # noqa: ARG002 # pyright: ignore[reportUnusedParameter]
        """Disconnected callback."""
        if self._expected_disconnect:
            logger.debug("%s: Disconnected from device; RSSI: %s", self.name, self.rssi)
            return
        logger.warning(
            "%s: Device unexpectedly disconnected; RSSI: %s",
            self.name,
            self.rssi,
        )

    def _disconnect(self) -> None:
        """Disconnect from device."""
        self._disconnect_timer = None
        asyncio.create_task(self._execute_timed_disconnect())  # noqa: RUF006 # pyright: ignore[reportUnusedCallResult]

    async def _execute_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        logger.debug(
            "%s: Disconnecting after timeout of %s",
            self.name,
            DISCONNECT_DELAY,
        )
        await self._execute_disconnect()

    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        async with self._connect_lock:
            client = self._client
            self._expected_disconnect = True
            self._client = None
            self._write_char = None
            if client and client.is_connected:
                await client.disconnect()  # pyright: ignore[reportUnusedCallResult]

    @retry_bluetooth_connection_error(DEFAULT_ATTEMPTS)
    async def _send_command_locked(self, commands: list[bytes]) -> None:
        """Send command to device and read response."""
        try:
            await self._execute_command_locked(commands)
        except BleakDBusError as ex:
            # Disconnect so we can reset state and try again
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
            # Disconnect so we can reset state and try again
            logger.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s", self.name, self.rssi, ex
            )
            await self._execute_disconnect()
            raise

    async def _send_command(self, commands: list[bytes] | bytes) -> None:
        """Send command to device and read response."""
        await self._ensure_connected()
        if not isinstance(commands, list):
            commands = [commands]
        await self._send_command_while_connected(commands)

    async def _send_command_while_connected(self, commands: list[bytes]) -> None:
        """Send command to device and read response."""
        logger.debug(
            "%s: Sending commands %s",
            self.name,
            [command.hex() for command in commands],
        )
        if self._operation_lock.locked():
            logger.debug(
                "%s: Operation already in progress, waiting for it to complete; RSSI: %s",  # noqa: E501
                self.name,
                self.rssi,
            )
        async with self._operation_lock:
            try:
                return await self._send_command_locked(commands)
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

    async def _execute_command_locked(self, commands: list[bytes]) -> None:
        """Execute command and read response."""
        assert self._client is not None  # noqa: S101
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")
        for command in commands:
            await self._client.write_gatt_char(
                self._write_char, command, response=False
            )

    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> bool:
        """Resolve characteristics."""
        if char := services.get_characteristic(WRITE_CHARACTERISTIC_UUID):
            self._write_char = char
        return bool(self._write_char)
