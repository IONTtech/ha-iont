"""Support for IONT binary sensor entities."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from pyiont import ConnectionState, Connector, IontCharger, VehicleState

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import IontConfigEntry
from .entity import IontChargerEntity, IontConnectorEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IontChargerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an IONT binary sensor entity on the charger device."""

    is_on_fn: Callable[[IontCharger], bool | None]


@dataclass(frozen=True, kw_only=True)
class IontConnectorBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an IONT binary sensor entity on a connector sub-device."""

    is_on_fn: Callable[[Connector], bool | None]


def _online(connector: Connector) -> bool | None:
    """Whether the connector's controller answers the charger; unknown while it is."""
    if connector.connection_state in (None, ConnectionState.UNKNOWN):
        return None
    return connector.connection_state is ConnectionState.ONLINE


def _vehicle_connected(connector: Connector) -> bool | None:
    """Whether a vehicle is plugged in; unknown while the state is, or in error."""
    if connector.vehicle_state in (
        None,
        VehicleState.UNKNOWN,
        VehicleState.ERROR,
    ):
        return None
    return connector.vehicle_state is not VehicleState.NOT_CONNECTED


def _problem(connector: Connector) -> bool | None:
    """Whether the connector reports a vehicle or cable error."""
    if connector.vehicle_state in (None, VehicleState.UNKNOWN):
        return None
    return connector.vehicle_state is VehicleState.ERROR


CHARGER_BINARY_SENSORS: tuple[IontChargerBinarySensorEntityDescription, ...] = (
    IontChargerBinarySensorEntityDescription(
        key="free_charging",
        translation_key="free_charging",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda charger: charger.device.free_charging,
    ),
)

CONNECTOR_BINARY_SENSORS: tuple[IontConnectorBinarySensorEntityDescription, ...] = (
    IontConnectorBinarySensorEntityDescription(
        key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=lambda connector: connector.charging,
    ),
    IontConnectorBinarySensorEntityDescription(
        key="authorized",
        translation_key="authorized",
        is_on_fn=lambda connector: connector.authorized,
    ),
    IontConnectorBinarySensorEntityDescription(
        key="vehicle_connected",
        translation_key="vehicle_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=_vehicle_connected,
    ),
    IontConnectorBinarySensorEntityDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_problem,
    ),
    IontConnectorBinarySensorEntityDescription(
        key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_online,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IontConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IONT binary sensor entities based on a config entry."""
    coordinator = entry.runtime_data

    entities: list[BinarySensorEntity] = [
        IontChargerBinarySensorEntity(coordinator, description)
        for description in CHARGER_BINARY_SENSORS
    ]
    entities.extend(
        IontConnectorBinarySensorEntity(coordinator, description, number=number)
        for number in range(1, coordinator.charger.connector_count + 1)
        for description in CONNECTOR_BINARY_SENSORS
    )

    async_add_entities(entities)


class IontChargerBinarySensorEntity(IontChargerEntity, BinarySensorEntity):
    """Defines an IONT binary sensor entity on the charger device."""

    entity_description: IontChargerBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self.entity_description.is_on_fn(self.coordinator.charger)


class IontConnectorBinarySensorEntity(IontConnectorEntity, BinarySensorEntity):
    """Defines an IONT binary sensor entity on a connector sub-device."""

    entity_description: IontConnectorBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self.entity_description.is_on_fn(self.connector)
