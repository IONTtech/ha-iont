"""Support for IONT button entities."""

from typing import override

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import IontConfigEntry
from .entity import IontConnectorEntity, iont_exception_handler

PARALLEL_UPDATES = 1

BOOST = ButtonEntityDescription(
    key="boost",
    translation_key="boost",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IontConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IONT button entities based on a config entry."""
    coordinator = entry.runtime_data

    # Boost addresses a connector by its OCPP connector ID, so a connector
    # without one has nothing to press.
    async_add_entities(
        IontBoostButtonEntity(coordinator, BOOST, number=number)
        for number, connector in enumerate(coordinator.charger.connectors, 1)
        if connector.connector_id
    )


class IontBoostButtonEntity(IontConnectorEntity, ButtonEntity):
    """Authorizes charging at full power, even under the eco strategy.

    Under eco the charger waits for surplus power before it charges; boost
    lets one session skip that wait and take what the installation allows.
    """

    @iont_exception_handler
    @override
    async def async_press(self) -> None:
        """Authorize the connector with boost."""
        await self.coordinator.charger.async_authorize(self._number, boost=True)
