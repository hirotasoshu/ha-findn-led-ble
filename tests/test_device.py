"""Tests for Findn LED device state handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bleak.backends.device import BLEDevice

from custom_components.findn_led_ble.device import FindnLedDevice
from custom_components.findn_led_ble.device_protocol import (
    EFFECTS_LIST,
    EffectDirection,
)

if TYPE_CHECKING:
    import pytest

IDENTIFY_COMMAND_COUNT = 4


class FakeTransport:
    """Fake BLE transport for device tests."""

    address = "AA:BB:CC:DD:EE:FF"
    name = "Findn Test"
    rssi = -55

    def __init__(self) -> None:
        """Initialize the fake transport."""
        self.commands: list[bytes] = []
        self.connected = False
        self.disconnected = False

    async def disconnect(self) -> None:
        """Record disconnect calls."""
        self.disconnected = True

    async def ensure_connected(self) -> None:
        """Record connection checks."""
        self.connected = True

    def update_ble_device(self, ble_device: object, advertisement_data: object) -> None:
        """Accept discovery updates."""

    async def write(self, commands: list[bytes] | bytes) -> None:
        """Record written commands."""
        self.commands.extend(commands if isinstance(commands, list) else [commands])


def _device_with_transport() -> tuple[FindnLedDevice, FakeTransport]:
    """Create a FindnLedDevice backed by a fake transport."""
    transport = FakeTransport()
    device = FindnLedDevice(
        BLEDevice("AA:BB:CC:DD:EE:FF", "Findn Test", {}), transport=transport
    )
    return device, transport


async def test_turn_on_updates_state_after_command_write() -> None:
    """Test turn_on writes before publishing optimistic state."""
    device, transport = _device_with_transport()
    callback_states: list[bool] = []

    def _record_state() -> None:
        callback_states.append(device.is_on)

    device.set_state_changed_callback(_record_state)

    await device.turn_on()

    assert transport.commands
    assert device.is_on is True
    assert callback_states == [True]


async def test_set_hs_color_clears_current_effect() -> None:
    """Test setting a color exits effect mode."""
    device, _transport = _device_with_transport()

    await device.set_effect(EFFECTS_LIST[0], EffectDirection.FORWARD)
    await device.set_hs_color((120.0, 75.0))

    assert device.effect is None
    assert device.hs == (120.0, 75.0)


async def test_identify_blinks_without_leaving_light_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test config-flow identification writes a complete blink sequence."""
    device, transport = _device_with_transport()

    async def _skip_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.findn_led_ble.device.asyncio.sleep", _skip_sleep
    )

    await device.identify()

    assert transport.connected is True
    assert len(transport.commands) == IDENTIFY_COMMAND_COUNT
    assert device.is_on is False
