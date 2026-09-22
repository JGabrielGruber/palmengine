"""
Post-build product packaging — shared by ApplicationHost and host-less ServerContext.

``core_service_registry().build_all`` constructs services. This module applies the
**product identity** steps both composition roots must share so MCP lean and full
host do not drift (BI-003 residual):

- slot map from ``built``
- ``assist.bind_analytics`` when both are present
- durable dashboard store when storage is ready
- design contributors + service-domain CQRS wire

Host-only packaging (projections, workplane, multi-runtime command router) stays
on :class:`~palm.app.host.application_host.ApplicationHost`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.services._cqrs_wiring import wire_all_service_cqrs
from palm.services.design.contributors import wire_builtin_design_contributors


@dataclass(frozen=True)
class ProductServiceBag:
    """Named product service slots after ``build_all`` + packaging."""

    inspect: Any | None = None
    session: Any | None = None
    definitions: Any | None = None
    execution: Any | None = None
    assist: Any | None = None
    design: Any | None = None
    analytics: Any | None = None


def bag_from_built(built: dict[str, Any]) -> ProductServiceBag:
    """Map a ``build_all`` result into named product slots."""
    return ProductServiceBag(
        inspect=built.get("inspect"),
        session=built.get("session"),
        definitions=built.get("definitions"),
        execution=built.get("execution"),
        assist=built.get("assist"),
        design=built.get("design"),
        analytics=built.get("analytics"),
    )


def apply_product_packaging(
    built: dict[str, Any],
    *,
    command_bus: CommandBus,
    query_bus: QueryBus,
    repository: Any,
    instance_manager: Any,
    storage: Any | None = None,
) -> ProductServiceBag:
    """Apply shared post-build product packaging; return the service bag.

    Safe to call from both host ``_wire_cqrs`` and host-less ``ServerContext``.
    Does not touch workplane, projections, or multi-runtime routing.
    """
    bag = bag_from_built(built)
    if bag.assist is not None and bag.analytics is not None:
        bag.assist.bind_analytics(bag.analytics)
    if storage is not None and getattr(storage, "is_initialized", False):
        from palm.services.analytics.dashboards import attach_dashboard_store

        attach_dashboard_store(storage)
    if bag.design is not None:
        wire_builtin_design_contributors()
    wire_all_service_cqrs(
        command_bus,
        query_bus,
        repository=repository,
        instance_manager=instance_manager,
        design=bag.design,
        execution=bag.execution,
    )
    return bag


__all__ = [
    "ProductServiceBag",
    "apply_product_packaging",
    "bag_from_built",
]
