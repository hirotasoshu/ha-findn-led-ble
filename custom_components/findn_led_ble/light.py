"""Light platform for findn_led_ble."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityDescription,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .entity import FindnLedEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FindnLedDataUpdateCoordinator
    from .data import FindnLedConfigEntry

ENTITY_DESCRIPTIONS = (
    LightEntityDescription(
        key="findn_led_ble",
        name="Findn LED BLE strip",
        icon="mdi:led-strip-variant",
        has_entity_name=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 # pyright: ignore[reportUnusedParameter]
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


class FindnLedLight(FindnLedEntity, LightEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """findn_led_ble light class."""

    _attr_supported_color_modes: set[ColorMode] | set[str] | None = {ColorMode.HS}  # noqa: RUF012

    def __init__(
        self,
        coordinator: FindnLedDataUpdateCoordinator,
        entity_description: LightEntityDescription,
    ) -> None:
        """Initialize the light class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.device = coordinator.config_entry.runtime_data.device
        self.device.set_update_callback(self._handle_coordinator_update)

        self._attr_unique_id = self.device.address
        self._attr_device_info = dr.DeviceInfo(
            name=self.device.name,
            connections={(dr.CONNECTION_BLUETOOTH, self.device.address)},
        )
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_brightness = self.device.brightness
        self._attr_hs_color = self.device.hs
        self._attr_is_on = self.device.is_on
        self._attr_effect = self.device.effect

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:  # pyright: ignore[reportAny]
        """Instruct the light to turn on."""
        if hs := kwargs.get(ATTR_HS_COLOR):
            await self.device.set_hs_color(hs)  # pyright: ignore[reportAny]
        if brightness := kwargs.get(ATTR_BRIGHTNESS):
            await self.device.set_brightness(brightness)  # pyright: ignore[reportAny]
        if effect := kwargs.get(ATTR_EFFECT):
            effect = int(effect, base=0)
            await self.device.set_effect(effect)  # pyright: ignore[reportAny]
        if not self.device.is_on:
            await self.device.turn_on()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:  # pyright: ignore[reportAny]
        """Instruct the light to turn off."""
        await self.device.turn_off()

    @override
    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:  # pyright: ignore[reportAny]
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()
