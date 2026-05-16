"""Light platform for findn_led_ble."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import voluptuous as vol
from homeassistant.components import light
from homeassistant.components.light.const import ColorMode, LightEntityFeature
from homeassistant.core import callback
from homeassistant.helpers import entity_platform

from custom_components.findn_led_ble import device_protocol
from custom_components.findn_led_ble.const import SERVICE_SET_EFFECT
from custom_components.findn_led_ble.entity import FindnLedEntity

if TYPE_CHECKING:
    from custom_components.findn_led_ble.data import FindnLedConfigEntry
    from custom_components.findn_led_ble.device import FindnLedDevice

EFFECTS_LIST_WITH_OFF = (light.EFFECT_OFF, *device_protocol.EFFECTS_LIST)

ENTITY_DESCRIPTIONS = (
    light.LightEntityDescription(
        key="findn_led_ble",
        name="Findn LED BLE strip",
        icon="mdi:led-strip-variant",
        has_entity_name=True,
    ),
)


def _set_effect_schema() -> Any:  # pyright: ignore[reportExplicitAny]
    """Return schema for the set_effect service."""
    return {
        vol.Required("effect"): vol.In(EFFECTS_LIST_WITH_OFF),
        vol.Optional("direction", default="forward"): vol.In(["forward", "backward"]),
    }


async def async_setup_entry(
    _: object,
    entry: FindnLedConfigEntry,
    async_add_entities: entity_platform.AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    async_add_entities(
        FindnLedLight(
            entry=entry,
            device=entry.runtime_data.device,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    # Add services using entity platform
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_EFFECT,
        _set_effect_schema(),
        "async_set_effect",
    )


class FindnLedLight(FindnLedEntity, light.LightEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """findn_led_ble light class."""

    _attr_supported_color_modes: set[ColorMode] | None = {  # noqa: RUF012
        ColorMode.HS,
    }

    def __init__(
        self,
        entry: FindnLedConfigEntry,
        device: FindnLedDevice,
        entity_description: light.LightEntityDescription,
    ) -> None:
        """Initialize the light class."""
        super().__init__(entry, device)
        self.entity_description: light.LightEntityDescription = entity_description  # pyright: ignore[reportIncompatibleVariableOverride]
        self.device.register_state_changed_callback(self._handle_device_update)
        self._attr_supported_features: LightEntityFeature = LightEntityFeature.EFFECT  # pyright: ignore[reportIncompatibleVariableOverride]
        self._attr_effect_list: list[str] | None = list(EFFECTS_LIST_WITH_OFF)
        self._async_update_attrs()

    @override
    async def async_will_remove_from_hass(self) -> None:
        """Disconnect entity from device state callbacks."""
        self.device.register_state_changed_callback(None)

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_brightness: int | None = self.device.brightness
        self._attr_hs_color: tuple[float, float] | None = self.device.hs
        self._attr_is_on: bool | None = self.device.is_on

        current_effect = self.device.effect
        if current_effect:
            self._attr_effect: str | None = current_effect
            self._attr_color_mode: ColorMode | None = ColorMode.BRIGHTNESS
        else:
            self._attr_effect = light.EFFECT_OFF
            self._attr_color_mode = ColorMode.HS

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Instruct the light to turn on."""
        if not self.device.is_on:
            await self.device.turn_on()
        hs = kwargs.get(light.ATTR_HS_COLOR)
        if hs:
            await self.device.set_hs_color(hs)  # pyright: ignore[reportAny]
        brightness = kwargs.get(light.ATTR_BRIGHTNESS)
        if brightness:
            await self.device.set_brightness(brightness)  # pyright: ignore[reportAny]
        effect = kwargs.get(light.ATTR_EFFECT)
        if effect:
            if effect == light.EFFECT_OFF:
                await self.device.clear_effect()
            else:
                await self.device.set_effect(
                    effect, device_protocol.EffectDirection.FORWARD
                )  # pyright: ignore[reportAny]

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Instruct the light to turn off."""
        await self.device.turn_off()

    async def async_set_effect(
        self,
        effect: str,
        direction: device_protocol.EffectDirection = (
            device_protocol.EffectDirection.FORWARD
        ),
    ) -> None:
        """Set effect with direction service."""
        if effect == light.EFFECT_OFF:
            await self.device.clear_effect()
        else:
            await self.device.set_effect(effect, direction)

    @callback
    def _handle_device_update(self) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()
