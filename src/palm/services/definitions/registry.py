"""Definitions service contract — catalog verbs (transport-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResourceKind = Literal["flows", "processes", "resources"]
CatalogOperation = Literal["list", "get", "validate", "create", "update", "delete"]


@dataclass(frozen=True)
class CatalogVerb:
    """Declarative catalog operation owned by the definitions domain."""

    verb_id: str
    resource_kind: ResourceKind
    operation: CatalogOperation
    summary: str = ""


_registry: list[CatalogVerb] = [
    CatalogVerb("list_flows", "flows", "list", "List flow definitions"),
    CatalogVerb("get_flow", "flows", "get", "Get flow definition"),
    CatalogVerb("validate_flow", "flows", "validate", "Validate flow definition"),
    CatalogVerb("create_flow", "flows", "create", "Create flow definition"),
    CatalogVerb("update_flow", "flows", "update", "Update flow definition"),
    CatalogVerb("delete_flow", "flows", "delete", "Delete flow definition"),
    CatalogVerb("list_processes", "processes", "list", "List process definitions"),
    CatalogVerb("get_process", "processes", "get", "Get process definition"),
    CatalogVerb("create_process", "processes", "create", "Create process definition"),
    CatalogVerb("update_process", "processes", "update", "Update process definition"),
    CatalogVerb("delete_process", "processes", "delete", "Delete process definition"),
    CatalogVerb("list_resources", "resources", "list", "List resource definitions"),
    CatalogVerb("get_resource", "resources", "get", "Get resource definition"),
    CatalogVerb("create_resource", "resources", "create", "Create resource definition"),
    CatalogVerb("update_resource", "resources", "update", "Update resource definition"),
    CatalogVerb("delete_resource", "resources", "delete", "Delete resource definition"),
]


def catalog_verbs() -> tuple[CatalogVerb, ...]:
    return tuple(_registry)


__all__ = ["CatalogOperation", "CatalogVerb", "ResourceKind", "catalog_verbs"]