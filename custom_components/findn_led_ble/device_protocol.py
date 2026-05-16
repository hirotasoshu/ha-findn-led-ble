"""Findn LED BLE device protocol."""

from enum import StrEnum, auto
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from homeassistant.util.color import brightness_to_value, color_RGB_to_hs

if TYPE_CHECKING:
    from collections.abc import Mapping

EFFECT_TO_BYTE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "Automatic loop": 0x1,
        "Symphony": 0x2,
        "Colorful energy": 0x3,
        "Colorful jumps": 0x4,
        "7 colors stobe": 0x7,
        "7 colors gradient": 0xA,
        "Colorful fluttering": 0x1A,
        "Red-green-blue fluttering": 0x1B,
        "Colorful brushing": 0x1D,
        "Red-green-blue color brushing": 0x1E,
        "Yellow-cyan-purple color brushing": 0x1F,
        "Colorful brush color brush closed-pull": 0x20,
        "White opening-closing": 0x2C,
        "Puprle opening-closing": 0x2B,
        "Cyan opening-closing": 0x2A,
        "Yellow opening-closing": 0x29,
        "Blue opening-closing": 0x28,
        "Green opening-closing": 0x27,
        "Red opening-closing": 0x26,
        "Yellow-cyan-purple opening-closing": 0x25,
        "Red-green-blue opening-closing": 0x24,
        "7 colors opening-closing": 0x23,
        "7 colors light-dark transition": 0x2D,
        "Blue-red-green light-dark transition": 0x2E,
        "Violent-green-yellow light-dark transition": 0x2F,
        "6 colors light-dark transition red": 0x30,
        "6 colors light-dark transition green": 0x31,
        "6 colors light-dark transition blue": 0x32,
        "6 colors light-dark transition cyan": 0x33,
        "6 colors light-dark transition yellow": 0x34,
        "6 colors light-dark transition purple": 0x35,
        "6 colors light-dark transition white": 0x36,
        "Blue-purple running water": 0x3E,
        "Yellow-cyan running water": 0x3D,
        "Yellow-blue running water": 0x3C,
        "Green-blue running water": 0x3B,
        "Red-green running water": 0x3A,
        "Purple-green-yellow running water": 0x39,
        "Blue-green-red running water": 0x38,
        "7 colors flowing water": 0x37,
        "7 colors tailing": 0x4C,
        "Red tailing": 0x4D,
        "Green tailing": 0x4E,
        "Blue tailing": 0x4F,
        "Yellow tailing": 0x50,
        "Cyan tailing": 0x51,
        "Purple tailing": 0x52,
        "White tailing": 0x53,
        "7 colors running": 0x5B,
        "Blue-green-red running": 0x5C,
        "Purple-cyan-yellow running": 0x5D,
        "White running": 0x5A,
        "Purple running": 0x59,
        "Cyan running": 0x58,
        "Yellow running": 0x57,
        "Blue running": 0x56,
        "Green running": 0x55,
        "Red running": 0x54,
    }
)
EFFECTS_LIST: Final[list[str]] = list(EFFECT_TO_BYTE.keys())
BYTE_MODULUS: Final[int] = 256


class EffectDirection(StrEnum):
    """Effect direction enum."""

    FORWARD = auto()
    BACKWARD = auto()


class FindnLedBLEProtocol:
    """Protocol for Findn LED BLE strip."""

    _turn_on_command: Final[bytes] = bytes([0xBC, 0x1, 0x1, 0x1, 0x55])
    _turn_off_command: Final[bytes] = bytes([0xBC, 0x1, 0x1, 0x0, 0x55])

    _brightness_scale_range: Final[tuple[int, int]] = (100, 1000)

    @cached_property
    def turn_on_command(self) -> bytes:
        """Turn ON command."""
        return self._turn_on_command

    @cached_property
    def turn_off_command(self) -> bytes:
        """Turn OFF command."""
        return self._turn_off_command

    def construct_set_brightness_cmd(self, brightness: int) -> bytes:
        """
        Construct command to set brightness.

        Input brighntess must be in range 1..255 (as in HA).
        That brighntess value is scaled to be in range 1..1000.
        After that, we construct cmd like this:

        0xBC 0x05 0x06 scaled_brightess//256 scaled_brightness%256 0x00 0x00 0x00 0x00 0x55
        """  # noqa: E501
        scaled_brightness = round(
            brightness_to_value(self._brightness_scale_range, brightness)
        )
        return bytes(
            [
                0xBC,
                0x5,
                0x6,
                scaled_brightness // BYTE_MODULUS,
                scaled_brightness % BYTE_MODULUS,
                0x0,
                0x0,
                0x0,
                0x0,
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
                0x4,
                0x6,
                hue // BYTE_MODULUS,
                hue % BYTE_MODULUS,
                saturation // BYTE_MODULUS,
                saturation % BYTE_MODULUS,
                0x0,
                0x0,
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
        effect_byte = self._get_effect_byte(effect_name)
        direction_value = 0 if direction == EffectDirection.BACKWARD else 1
        return [
            bytes([0xBC, 0x6, 0x2, 0x0, effect_byte, 0x55]),
            bytes([0xBC, 0x7, 0x1, direction_value, 0x55]),
        ]

    def _get_effect_byte(self, effect_name: str) -> int:
        """Get effect byte by name."""
        try:
            return EFFECT_TO_BYTE[effect_name]
        except KeyError as error:
            raise ValueError(f"Unknown effect: {effect_name}") from error
