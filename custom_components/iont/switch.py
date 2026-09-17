"""Support for IONT switch entities."""

from typing import Any, override

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import IontConfigEntry
from .entity import IontConnectorEntity, iont_exception_handler

PARALLEL_UPDATES = 1

AUTHORIZATION = SwitchEntityDescription(
    key="authorization",
    translation_key="authorization",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IontConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IONT switch entities based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        IontAuthorizationSwitchEntity(coordinator, AUTHORIZATION, number=number)
        for number in range(1, coordinator.charger.connector_count + 1)
    )


class IontAuthorizationSwitchEntity(IontConnectorEntity, SwitchEntity):
    """Authorizes charging on a connector, the way a card or an app would.

    On means the connector holds an authorization and charges as soon as a
    vehicle asks for power; off withdraws it and stops a running session.
    """

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the connector is authorized."""
        return self.connector.authorized

    @iont_exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Authorize charging on the connector."""
        await self.coordinator.charger.async_authorize(self._number)

    @iont_exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Withdraw the connector's authorization."""
        await self.coordinator.charger.async_deauthorize(self._number)
