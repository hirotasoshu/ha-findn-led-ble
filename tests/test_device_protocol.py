"""Tests for Findn LED BLE protocol commands."""

from __future__ import annotations

import pytest

from custom_components.findn_led_ble.device_protocol import (
    EffectDirection,
    FindnLedBLEProtocol,
)


@pytest.fixture
def protocol() -> FindnLedBLEProtocol:
    """Return a protocol instance."""
    return FindnLedBLEProtocol()


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        ("turn_on_command", "bc01010155"),
        ("turn_off_command", "bc01010055"),
    ],
)
def test_power_command(
    protocol: FindnLedBLEProtocol, attribute: str, expected: str
) -> None:
    """Test power command bytes."""
    assert getattr(protocol, attribute) == bytes.fromhex(expected)


@pytest.mark.parametrize(
    ("brightness", "expected"),
    [
        (1, "bc050600670000000055"),
        (128, "bc050602270000000055"),
        (255, "bc050603e80000000055"),
    ],
)
def test_construct_set_brightness_cmd(
    protocol: FindnLedBLEProtocol, brightness: int, expected: str
) -> None:
    """Test brightness command bytes."""
    assert protocol.construct_set_brightness_cmd(brightness) == bytes.fromhex(expected)


def test_construct_set_hs_color_cmd(protocol: FindnLedBLEProtocol) -> None:
    """Test HS color command bytes."""
    assert protocol.construct_set_hs_color_cmd((120.0, 75.0)) == bytes.fromhex(
        "bc0406007802ee000055"
    )


def test_construct_set_effect_cmd_forward(protocol: FindnLedBLEProtocol) -> None:
    """Test forward effect command bytes."""
    assert protocol.construct_set_effect_cmd("Symphony", EffectDirection.FORWARD) == [
        bytes.fromhex("bc0602000255"),
        bytes.fromhex("bc07010155"),
    ]


def test_construct_set_effect_cmd_backward(protocol: FindnLedBLEProtocol) -> None:
    """Test backward effect command bytes."""
    assert protocol.construct_set_effect_cmd("Symphony", EffectDirection.BACKWARD) == [
        bytes.fromhex("bc0602000255"),
        bytes.fromhex("bc07010055"),
    ]


def test_set_effect_cmd_rejects_unknown_effect(
    protocol: FindnLedBLEProtocol,
) -> None:
    """Test unknown effect names are rejected."""
    with pytest.raises(ValueError, match="Unknown effect"):
        protocol.construct_set_effect_cmd("Unknown")
