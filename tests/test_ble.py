"""Tests for Findn LED BLE transport."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.device import BLEDevice

from custom_components.findn_led_ble.ble import (
    CharacteristicMissingError,
    FindnLedBleTransport,
)

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic

EXPECTED_WRITE_COUNT = 2


class FakeServices:
    """Fake BLE service collection."""

    def __init__(self, characteristic: BleakGATTCharacteristic | object) -> None:
        """Initialize fake services."""
        self.characteristic = characteristic

    def get_characteristic(self, _uuid: str) -> BleakGATTCharacteristic | object:
        """Return the configured characteristic."""
        return self.characteristic


class FakeClient:
    """Fake BLE client."""

    def __init__(self) -> None:
        """Initialize the fake client."""
        self.is_connected = True
        self.services = FakeServices(object())
        self.clear_cache = AsyncMock()
        self.disconnect = AsyncMock(side_effect=self._disconnect)
        self.write_gatt_char = AsyncMock()

    async def _disconnect(self) -> None:
        """Mark the fake client disconnected."""
        self.is_connected = False


async def test_write_reuses_connected_client() -> None:
    """Test command writes keep and reuse an active BLE connection."""
    client = FakeClient()
    transport = FindnLedBleTransport(BLEDevice("AA:BB:CC:DD:EE:FF", "Findn Test", {}))

    with (
        patch(
            "custom_components.findn_led_ble.ble.close_stale_connections",
            new=AsyncMock(),
        ) as close_stale_connections,
        patch(
            "custom_components.findn_led_ble.ble.establish_connection",
            new=AsyncMock(return_value=client),
        ) as establish_connection,
    ):
        await transport.write(b"first")
        await transport.write(b"second")
        await transport.disconnect()
        close_stale_connections.assert_awaited_once()
        establish_connection.assert_awaited_once()

    assert client.write_gatt_char.await_count == EXPECTED_WRITE_COUNT
    client.disconnect.assert_awaited_once()


async def test_missing_characteristic_clears_cache() -> None:
    """Test stale service cache is cleared when the write characteristic is absent."""
    client = FakeClient()
    client.services = FakeServices(None)
    transport = FindnLedBleTransport(BLEDevice("AA:BB:CC:DD:EE:FF", "Findn Test", {}))

    with (
        patch(
            "custom_components.findn_led_ble.ble.close_stale_connections",
            new=AsyncMock(),
        ),
        patch(
            "custom_components.findn_led_ble.ble.establish_connection",
            new=AsyncMock(return_value=client),
        ),
        pytest.raises(CharacteristicMissingError),
    ):
        await transport.write(b"command")

    client.clear_cache.assert_awaited_once()
    client.disconnect.assert_awaited_once()
