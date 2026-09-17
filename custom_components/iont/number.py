"""Support for IONT number entities."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from pyiont import EXTERNAL_POWER_LIMIT_MAX, SUBSYSTEM_SETTINGS, IontCharger

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import IontConfigEntry
from .entity import IontChargerEntity, iont_exception_handler

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class IontNumberEntityDescription(NumberEntityDescription):
    """Describes an IONT number entity."""

    value_fn: Callable[[IontCharger], float | None]
    set_fn: Callable[[IontCharger, float], Awaitable[Any]]


NUMBERS: tuple[IontNumberEntityDescription, ...] = (
    IontNumberEntityDescription(
        key="external_power_limit",
        translation_key="external_power_limit",
        device_class=NumberDeviceClass.POWER,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=EXTERNAL_POWER_LIMIT_MAX,
        native_step=1,
        value_fn=lambda charger: charger.settings.external_power_limit,
        set_fn=lambda charger, value: charger.async_set_external_power_limit(
            int(value)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IontConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IONT number entities based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        IontNumberEntity(coordinator, description, subsystem=SUBSYSTEM_SETTINGS)
        for description in NUMBERS
    )


class IontNumberEntity(IontChargerEntity, NumberEntity):
    """Defines an IONT number entity."""

    entity_description: IontNumberEntityDescription

    @property
    @override
    def native_value(self) -> float | None:
        """Return the value of the setting."""
        return self.entity_description.value_fn(self.coordinator.charger)

    @iont_exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Write the setting to the charger."""
        await self.entity_description.set_fn(self.coordinator.charger, value)
