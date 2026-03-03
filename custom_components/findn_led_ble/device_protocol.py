"""Findn LED BLE device protocol."""

from enum import StrEnum, auto
from functools import cached_property
from typing import Final

from homeassistant.util.color import brightness_to_value, color_RGB_to_hs

EFFECT_TO_ID: Final[dict[str, int]] = {
    "Test Effect": 1000,
}
EFFECTS_LIST: Final[list[str]] = list(EFFECT_TO_ID.keys())


class EffectDirection(StrEnum):
    """Effect direction enum."""

    FORWARD = auto()
    BACKWARD = auto()


class FindnLedBLEProtocol:
    """Protocol for Findn LED BLE strip."""

    _TURN_ON_CMD: Final[bytes] = bytes([0xBC, 0x01, 0x01, 0x01, 0x55])
    _TURN_OFF_CMD: Final[bytes] = bytes([0xBC, 0x01, 0x01, 0x00, 0x55])

    _BRIGHTESS_SCALE_RANGE: Final[tuple[int, int]] = (100, 1000)

    def __get_effect_id(self, effect_name: str) -> int:
        """Get effect ID by name."""
        if effect_name in EFFECT_TO_ID:
            return EFFECT_TO_ID[effect_name]
        raise ValueError(f"Unknown effect: {effect_name}")

    @cached_property
    def turn_on_command(self) -> bytes:
        """Turn ON command."""
        return self._TURN_ON_CMD

    @cached_property
    def turn_off_command(self) -> bytes:
        """Turn OFF command."""
        return self._TURN_OFF_CMD

    def construct_set_brightness_cmd(self, brightness: int) -> bytes:
        """
        Construct command to set brightness.

        Input brighntess must be in range 1..255 (as in HA).
        That brighntess value is scaled to be in range 1..1000.
        After that, we construct cmd like this:

        0xBC 0x05 0x06 scaled_brightess//256 scaled_brightness%256 0x00 0x00 0x00 0x00 0x55
        """  # noqa: E501
        scaled_brightness = round(
            brightness_to_value(self._BRIGHTESS_SCALE_RANGE, brightness)
        )
        return bytes(
            [
                0xBC,
                0x05,
                0x06,
                scaled_brightness // 256,
                scaled_brightness % 256,
                0x00,
                0x00,
                0x00,
                0x00,
                0x55,
            ]
        )

    def construct_set_hs_color_cmd(self, hs: tuple[float, float]) -> bytes:
        """
        Construct command to set color.

        Hue must be in degrees, saturation in % (as in HA).
        Saturation value is scaled to be in range 0..1000.
        After that, we construct cmd like this:

        0xBC 0x04 0x06 hue//256 hue%256 scaled_saturation//256 scaled_saturation%256 0x00 0x00 0x55
        """  # noqa: E501
        hue = round(hs[0])
        saturation = round(hs[1] * 10)
        return bytes(
            [
                0xBC,
                0x04,
                0x06,
                hue // 256,
                hue % 256,
                saturation // 256,
                saturation % 256,
                0x00,
                0x00,
                0x55,
            ]
        )

    def construct_set_rgb_color_cmd(self, rgb: tuple[int, int, int]) -> bytes:
        """Construct command to set color using rgb."""
        return self.construct_set_hs_color_cmd(color_RGB_to_hs(*rgb))

    def construct_set_effect_cmd(
        self, effect_name: str, direction: EffectDirection = EffectDirection.FORWARD
    ) -> list[bytes]:
        """Construct command to set effect."""
        effect_id = self.__get_effect_id(effect_name)
        direction_value = 1 if direction == EffectDirection.BACKWARD else 0
        return [
            bytes(
                [
                    0xBC,
                    0x06,
                    0x02,
                    effect_id // 256,
                    effect_id % 256,
                    0x55,
                ]
            ),
            bytes(
                [
                    0xBC,
                    0x07,
                    0x01,
                    direction_value,
                    0x55,
                ]
            ),
        ]
