"""Findn LED BLE Device."""

import asyncio
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Protocol

from custom_components.findn_led_ble.ble import FindnLedBleTransport
from custom_components.findn_led_ble.device_protocol import (
    EffectDirection,
    FindnLedBLEProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData


class FindnLedTransport(Protocol):
    """Transport interface used by FindnLedDevice."""

    @property
    def address(self) -> str:
        """Return the transport address."""

    @property
    def name(self) -> str:
        """Return the transport name."""

    @property
    def rssi(self) -> int | None:
        """Return latest transport RSSI."""

    async def disconnect(self) -> None:
        """Disconnect transport."""

    async def ensure_connected(self) -> None:
        """Ensure transport is connected."""

    def update_ble_device(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Update transport BLE device data."""

    async def write(self, commands: list[bytes] | bytes) -> None:
        """Write commands through transport."""


@dataclass(frozen=True)
class FindnLedState:
    """Findn LED state."""

    power: bool = False
    hs: tuple[float, float] = (0, 0)
    brightness: int = 1
    effect: str | None = None


IDENTIFY_SLEEP_DELAY = 0.2


class FindnLedDevice:
    """Findn LED BLE Device."""

    def __init__(
        self,
        ble_device: BLEDevice,
        advertisement_data: AdvertisementData | None = None,
        transport: FindnLedTransport | None = None,
    ) -> None:
        """Init the Findn LED BLE."""
        self._transport: FindnLedTransport = transport or FindnLedBleTransport(
            ble_device,
            advertisement_data,
        )
        self._state: FindnLedState = FindnLedState()
        self._state_changed_callback: Callable[[], None] | None = None
        self._protocol: FindnLedBLEProtocol = FindnLedBLEProtocol()

    def register_state_changed_callback(
        self, callback: Callable[[], None] | None
    ) -> None:
        """Set the state changed callback."""
        self._state_changed_callback = callback

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Set the ble device."""
        self._transport.update_ble_device(ble_device, advertisement_data)

    @property
    def address(self) -> str:
        """Return the address."""
        return self._transport.address

    @property
    def name(self) -> str:
        """Get the name of the device."""
        return self._transport.name

    @property
    def rssi(self) -> int | None:
        """Get the rssi of the device."""
        return self._transport.rssi

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
    def effect(self) -> str | None:
        """Return current effect."""
        return self._state.effect

    async def update(self) -> None:
        """Update the Findn LED BLE."""
        await self._transport.ensure_connected()

    async def turn_on(self) -> None:
        """Turn on."""
        await self._send_command(self._protocol.turn_on_command)
        self._state = replace(self._state, power=True)
        self._async_notify_state_changed()

    async def turn_off(self) -> None:
        """Turn off."""
        await self._send_command(self._protocol.turn_off_command)
        self._state = replace(self._state, power=False)
        self._async_notify_state_changed()

    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness."""
        await self._send_command(
            self._protocol.construct_set_brightness_cmd(brightness)
        )
        self._state = replace(self._state, brightness=brightness)
        self._async_notify_state_changed()

    async def set_hs_color(self, hs: tuple[float, float]) -> None:
        """Set color using hue and saturation."""
        await self._send_command(self._protocol.construct_set_hs_color_cmd(hs))
        self._state = replace(self._state, hs=hs, effect=None)
        self._async_notify_state_changed()

    async def clear_effect(self) -> None:
        """Remove effect, set previous color."""
        await self.set_hs_color(self._state.hs)

    async def set_effect(
        self, effect_name: str, direction: EffectDirection = EffectDirection.FORWARD
    ) -> None:
        """Set the effect."""
        await self._send_command(
            self._protocol.construct_set_effect_cmd(effect_name, direction)
        )
        self._state = replace(self._state, effect=effect_name)
        self._async_notify_state_changed()

    async def stop(self) -> None:
        """Stop the Findn LED BLE."""
        await self._transport.disconnect()

    async def identify(self) -> None:
        """Blink the strip to identify it during config flow."""
        await self.update()
        await self._blink_once()
        await self._blink_once()

    async def _send_command(self, commands: list[bytes] | bytes) -> None:
        """Send command to the BLE transport."""
        await self._transport.write(commands)

    def _async_notify_state_changed(self) -> None:
        """Notify Home Assistant that optimistic state changed."""
        if self._state_changed_callback:
            self._state_changed_callback()

    async def _blink_once(self) -> None:
        """Blink the strip once."""
        await self.turn_on()
        await asyncio.sleep(IDENTIFY_SLEEP_DELAY)
        await self.turn_off()
        await asyncio.sleep(IDENTIFY_SLEEP_DELAY)
