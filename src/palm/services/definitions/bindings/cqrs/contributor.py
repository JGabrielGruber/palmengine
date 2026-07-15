"""Register definitions service on the service CQRS contributor registry."""

from __future__ import annotations

from palm.common.cqrs.service_contributors import ServiceCqrsContributor, register_service_cqrs_contributor
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)
from palm.services.definitions.bindings.cqrs.wiring import (
    DefinitionsWireContext,
    wire_definitions_service_cqrs,
)


def register_definitions_cqrs_contributor() -> None:
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="definitions",
            command_types=DEFINITIONS_COMMAND_TYPES,
            query_types=DEFINITIONS_QUERY_TYPES,
            wire=wire_definitions_service_cqrs,
        )
    )


register_definitions_cqrs_contributor()

__all__ = ["DefinitionsWireContext", "register_definitions_cqrs_contributor"]