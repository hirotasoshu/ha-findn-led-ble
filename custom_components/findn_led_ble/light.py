"""Light platform for findn_led_ble."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    EFFECT_OFF,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.components.light.const import ColorMode, LightEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import async_get_current_platform

from .const import SERVICE_SET_EFFECT
from .device_protocol import EFFECTS_LIST, EffectDirection
from .entity import FindnLedEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FindnLedDataUpdateCoordinator
    from .data import FindnLedConfigEntry
    from .device import FindnLedDevice

EFFECTS_LIST_WITH_OFF = [EFFECT_OFF, *EFFECTS_LIST]

ENTITY_DESCRIPTIONS = (
    LightEntityDescription(
        key="findn_led_ble",
        name="Findn LED BLE strip",
        icon="mdi:led-strip-variant",
        has_entity_name=True,
    ),
)

SET_EFFECT_SCHEMA = vol.Schema(
    {
        vol.Required("effect"): vol.In(EFFECTS_LIST_WITH_OFF),
        vol.Optional("direction", default="forward"): vol.In(["forward", "backward"]),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(
    _: HomeAssistant,
    entry: FindnLedConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    async_add_entities(
        FindnLedLight(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    # Add services using entity platform
    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_EFFECT,
        SET_EFFECT_SCHEMA,
        "async_set_effect",
    )


class FindnLedLight(FindnLedEntity, LightEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """findn_led_ble light class."""

    _attr_supported_color_modes: set[ColorMode] | None = {  # noqa: RUF012
        ColorMode.HS,
        ColorMode.BRIGHTNESS,
    }

    def __init__(
        self,
        coordinator: FindnLedDataUpdateCoordinator,
        entity_description: LightEntityDescription,
    ) -> None:
        """Initialize the light class."""
        super().__init__(coordinator)
        self.entity_description: LightEntityDescription = entity_description  # pyright: ignore[reportIncompatibleVariableOverride]
        self.device: FindnLedDevice = coordinator.config_entry.runtime_data.device
        self.device.set_update_callback(self._handle_coordinator_update)

        self._attr_unique_id: str | None = self.device.address
        self._attr_device_info: dr.DeviceInfo | None = dr.DeviceInfo(
            name=self.device.name,
            connections={(dr.CONNECTION_BLUETOOTH, self.device.address)},
        )
        self._attr_supported_features: LightEntityFeature = LightEntityFeature.EFFECT  # pyright: ignore[reportIncompatibleVariableOverride]
        self._attr_effect_list: list[str] | None = EFFECTS_LIST_WITH_OFF
        self._async_update_attrs()

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
            self._attr_effect = EFFECT_OFF
            self._attr_color_mode = ColorMode.HS

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Instruct the light to turn on."""
        if not self.device.is_on:
            await self.device.turn_on()
        if hs := kwargs.get(ATTR_HS_COLOR):
            await self.device.set_hs_color(hs)  # pyright: ignore[reportAny]
        if brightness := kwargs.get(ATTR_BRIGHTNESS):
            await self.device.set_brightness(brightness)  # pyright: ignore[reportAny]
        if effect := kwargs.get(ATTR_EFFECT):
            if effect == EFFECT_OFF:
                await self.device.clear_effect()
            else:
                await self.device.set_effect(effect, EffectDirection.FORWARD)  # pyright: ignore[reportAny]

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Instruct the light to turn off."""
        await self.device.turn_off()

    async def async_set_effect(
        self, effect: str, direction: EffectDirection = EffectDirection.FORWARD
    ) -> None:
        """Set effect with direction service."""
        if effect == EFFECT_OFF:
            await self.device.clear_effect()
        else:
            await self.device.set_effect(effect, direction)

    @override
    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()
