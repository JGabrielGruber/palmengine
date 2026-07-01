"""Resource catalog API shapes for the definitions service."""

from __future__ import annotations

from typing import Any

from palm.common.resource.catalog import ResourceCatalogEntry


def resource_catalog_row(entry: ResourceCatalogEntry) -> dict[str, Any]:
    """Catalog list row for a resource definition."""
    return {
        "definition_id": entry.definition_id,
        "name": entry.name,
        "provider": entry.provider,
        "action": entry.action,
        "resource_id_template": entry.resource_id,
        "param_keys": list(entry.param_keys),
        "has_input_schema": entry.has_input_schema,
        "has_output_schema": entry.has_output_schema,
        "summary": entry.summary(),
    }


__all__ = ["resource_catalog_row"]