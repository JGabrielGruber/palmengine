"""Register design service on the service CQRS contributor registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.common.cqrs.service_contributors import ServiceCqrsContributor, register_service_cqrs_contributor
from palm.services.design.bindings.cqrs.registry import DESIGN_COMMAND_TYPES, DESIGN_QUERY_TYPES
from palm.services.design.bindings.cqrs.schemas import (
    DESIGN_COMMAND_SCHEMAS,
    DESIGN_QUERY_SCHEMAS,
)
from palm.services.design.bindings.cqrs.wiring import wire_design_service_cqrs

if TYPE_CHECKING:
    from palm.services.design.service import DesignService


@dataclass(frozen=True)
class DesignWireContext:
    """Bootstrap context for design CQRS wiring."""

    design: DesignService


def register_design_cqrs_contributor() -> None:
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="design",
            command_types=DESIGN_COMMAND_TYPES,
            query_types=DESIGN_QUERY_TYPES,
            command_schemas=DESIGN_COMMAND_SCHEMAS,
            query_schemas=DESIGN_QUERY_SCHEMAS,
            wire=lambda bus, qbus, ctx: wire_design_service_cqrs(
                bus,
                qbus,
                ctx.design if isinstance(ctx, DesignWireContext) else ctx,
            ),
        )
    )


register_design_cqrs_contributor()

__all__ = ["DesignWireContext", "register_design_cqrs_contributor"]