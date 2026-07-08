"""Resource preflight checks for doctor and operator tooling."""

from __future__ import annotations

from typing import Any

from palm.common.resource.catalog import ResourceCatalog
from palm.common.resource.resolver import resource_definition_resolver
from palm.definitions.resource import ResourceDefinition


def rest_resource_has_base_url(resource: ResourceDefinition) -> bool:
    """Return whether a REST resource can resolve a URL without runtime overrides."""
    resource_id = str(resource.resource_id or "")
    if resource_id.startswith("http://") or resource_id.startswith("https://"):
        return True
    base_url = resource.params.get("base_url")
    if base_url is None:
        return False
    text = str(base_url).strip()
    if not text:
        return False
    return not text.startswith("{{")


def rest_resources_missing_base_url(repository: Any) -> list[dict[str, str]]:
    """List REST resource definitions that lack a usable base_url."""
    catalog = ResourceCatalog(repository)
    missing: list[dict[str, str]] = []
    for entry in catalog.by_provider("rest"):
        resource = repository.get_resource(entry.name)
        if rest_resource_has_base_url(resource):
            continue
        missing.append(
            {
                "name": entry.name,
                "resource_id": entry.resource_id or "",
                "action": entry.action,
            }
        )
    return missing


def probe_check_health(runtime: Any) -> dict[str, Any]:
    """Optionally invoke check-health when configured; report pass/fail."""
    repository = getattr(runtime, "repository", None)
    if repository is None:
        return {"available": False, "reason": "repository unavailable"}

    try:
        resource = repository.get_resource("check-health")
    except Exception:
        return {"available": False, "reason": "check-health resource not registered"}

    if resource.provider != "rest":
        return {"available": False, "reason": "check-health is not a REST resource"}

    if not rest_resource_has_base_url(resource):
        return {
            "available": True,
            "skipped": True,
            "reason": "base_url not configured on check-health",
        }

    engine = getattr(runtime, "resource", None)
    if engine is None:
        return {"available": True, "skipped": True, "reason": "resource engine unavailable"}

    if not engine.is_initialized:
        engine.initialize(definition_resolver=resource_definition_resolver(repository))

    result = engine.invoke("check-health")
    payload: dict[str, Any] = {
        "available": True,
        "probe": "check-health",
        "success": result.success,
    }
    if not result.success:
        payload["error"] = result.error
    return payload


def build_resource_preflight(runtime: Any) -> dict[str, Any]:
    """Assemble REST resource preflight data for doctor reports."""
    repository = getattr(runtime, "repository", None)
    if repository is None:
        return {
            "rest_missing_base_url": [],
            "check_health": {"available": False, "reason": "repository unavailable"},
        }

    missing = rest_resources_missing_base_url(repository)
    return {
        "rest_missing_base_url": missing,
        "rest_missing_base_url_count": len(missing),
        "check_health": probe_check_health(runtime),
    }


__all__ = [
    "build_resource_preflight",
    "probe_check_health",
    "rest_resource_has_base_url",
    "rest_resources_missing_base_url",
]