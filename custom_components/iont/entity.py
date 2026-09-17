"""Base entities for the IONT integration.

Every connector is a sub-device of the charger. The config entry has no
device serial number to derive identities from, so every identity derives from
the entry ID instead.
"""

from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, override

from pyiont import (
    SUBSYSTEM_DEVICE,
    Connector,
    IontCommandError,
    IontConnectionError,
    IontError,
    connector_subsystem,
)

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import IontDataUpdateCoordinator


def connector_identifier(entry_id: str, number: int) -> str:
    """Return the device registry identifier of a connector sub-device."""
    return f"{entry_id}_connector_{number}"


class IontEntity(CoordinatorEntity[IontDataUpdateCoordinator]):
    """Defines an IONT entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IontDataUpdateCoordinator,
        description: EntityDescription,
        *,
        subsystem: str,
        key_prefix: str = "",
    ) -> None:
        """Initialize an IONT entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._subsystem = subsystem
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{key_prefix}{description.key}"
        )

    @property
    @override
    def available(self) -> bool:
        """Return whether this entity's sub-system answered the last poll.

        A poll can come back partial, and an entity that reports a value from
        an earlier read as if it were current is lying about the charger.
        """
        return super().available and self._subsystem not in self.coordinator.data.failed


class IontChargerEntity(IontEntity):
    """Defines an IONT entity on the charger device."""

    def __init__(
        self,
        coordinator: IontDataUpdateCoordinator,
        description: EntityDescription,
        *,
        subsystem: str = SUBSYSTEM_DEVICE,
    ) -> None:
        """Initialize an IONT charger entity."""
        super().__init__(coordinator, description, subsystem=subsystem)
        self._attr_device_info = coordinator.device_info


class IontConnectorEntity(IontEntity):
    """Defines an IONT entity on a connector sub-device."""

    def __init__(
        self,
        coordinator: IontDataUpdateCoordinator,
        description: EntityDescription,
        *,
        number: int,
    ) -> None:
        """Initialize an IONT connector entity for a 1-based connector number."""
        super().__init__(
            coordinator,
            description,
            subsystem=connector_subsystem(number),
            key_prefix=f"connector_{number}_",
        )
        self._number = number
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    connector_identifier(coordinator.config_entry.entry_id, number),
                )
            },
            manufacturer=MANUFACTURER,
            translation_key="connector",
            translation_placeholders={"number": str(number)},
            via_device_id=coordinator.charger_device_id,
        )

    @property
    def connector(self) -> Connector:
        """Return the connector this entity belongs to."""
        return self.coordinator.charger.connectors[self._number - 1]


def iont_exception_handler[_EntityT: IontEntity, **_P](
    func: Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, Any]],
) -> Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, None]]:
    """Decorate IONT commands to translate library errors.

    A command that went through changes what the charger reports, so the
    charger is read again right away to show the change without waiting for
    the next poll.
    """

    async def handler(self: _EntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except IontConnectionError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(error)},
            ) from error
        except IontCommandError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(error)},
            ) from error
        except IontError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_request",
                translation_placeholders={"error": str(error)},
            ) from error

        await self.coordinator.async_refresh()

    return handler
