"""Flow catalog API shapes for the definitions service."""

from __future__ import annotations

from typing import Any

from palm.definitions.flow import FlowDefinition
from palm.patterns.wizard.bindings.catalog import flow_step_slugs


def flow_catalog_row(flow: FlowDefinition) -> dict[str, Any]:
    """Catalog list row; wizard flows may include step slugs."""
    row = flow.catalog_summary()
    if flow.pattern == "wizard":
        slugs = flow_step_slugs(flow)
        if slugs:
            row["step_slugs"] = slugs
    return row


__all__ = ["flow_catalog_row", "flow_step_slugs"]