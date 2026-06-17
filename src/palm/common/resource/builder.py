"""Build :class:`~palm.core.behavior_tree.nodes.leaf.resource_leaf.ResourceLeaf` instances."""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree.nodes.leaf.resource_leaf import ResourceLeaf
from palm.core.resource import ResourceEngine


def build_resource_leaf(
    name: str,
    *,
    resource_engine: ResourceEngine | None = None,
    resource_ref: str | None = None,
    provider: str | None = None,
    action: str | None = None,
    resource_id: str | None = None,
    params: dict[str, Any] | None = None,
    output_key: str | None = None,
    error_key: str | None = None,
    trace_key: str | None = None,
) -> ResourceLeaf:
    """Construct a resource leaf from declarative step or stage configuration."""
    return ResourceLeaf(
        name,
        resource_engine=resource_engine,
        resource_ref=resource_ref,
        provider=provider,
        action=action,
        resource_id=resource_id,
        params=params,
        output_key=output_key,
        error_key=error_key,
        trace_key=trace_key,
    )


def resource_leaf_from_legacy_action(
    slug: str,
    *,
    resource_engine: ResourceEngine | None,
    resource_provider: str,
    resource_id: str | None = None,
    output_key: str | None = None,
) -> ResourceLeaf:
    """Map legacy wizard ``action`` steps (provider + id) to a resource leaf."""
    return build_resource_leaf(
        slug,
        resource_engine=resource_engine,
        provider=resource_provider,
        action="fetch",
        resource_id=resource_id,
        output_key=output_key,
    )