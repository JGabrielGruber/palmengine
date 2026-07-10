"""Resource preflight checks for doctor and operator tooling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.common.resource.catalog import ResourceCatalog
from palm.common.resource.document_storage import (
    build_tiered_preflight_stats,
    resolve_documents_root,
    resolve_kv_backend,
)
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


def build_kv_preflight(runtime: Any, repository: Any) -> dict[str, Any]:
    """Report KV provider catalog usage and resolved ``auto`` backend."""
    catalog = ResourceCatalog(repository)
    entries = catalog.by_provider("kv")
    storage = getattr(runtime, "storage", None)
    storage_backend_name = storage.backend_name if storage is not None else None
    try:
        backend_resolved = resolve_kv_backend(
            "auto",
            storage=storage,
            storage_backend_name=storage_backend_name,
        )
    except ValueError:
        backend_resolved = "memory"

    namespace_set: set[str] = set()
    uses_tiered = False
    tiered_hot_max_keys = 500
    for entry in entries:
        resource = repository.get_resource(entry.name)
        namespace_set.add(str(resource.params.get("namespace") or "default"))
        backend = str(resource.params.get("backend") or "auto").strip().lower()
        if backend == "tiered":
            uses_tiered = True
            configured = resource.params.get("hot_max_keys")
            if configured is not None:
                try:
                    tiered_hot_max_keys = max(1, int(configured))
                except (TypeError, ValueError):
                    pass
    namespaces = sorted(namespace_set)

    payload: dict[str, Any] = {
        "resource_count": len(entries),
        "backend_resolved": backend_resolved,
        "storage_backend": storage_backend_name,
        "namespaces": namespaces,
    }
    if uses_tiered:
        primary_namespace = namespaces[0] if namespaces else "default"
        payload["tiered"] = build_tiered_preflight_stats(
            runtime,
            storage,
            namespace=primary_namespace,
            hot_max_keys=tiered_hot_max_keys,
        )
    return payload


def _documents_root_writable(root: Path) -> bool:
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".palm_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def build_file_preflight(runtime: Any, repository: Any) -> dict[str, Any]:
    """Report ``file`` document resources and documents_root writability."""
    catalog = ResourceCatalog(repository)
    entries = catalog.by_provider("file")
    if not entries:
        return {
            "resource_count": 0,
            "documents_root": None,
            "writable": None,
            "provider_installed": _file_provider_installed(),
        }

    root = resolve_documents_root(runtime)
    return {
        "resource_count": len(entries),
        "documents_root": str(root.resolve()),
        "writable": _documents_root_writable(root),
        "provider_installed": _file_provider_installed(),
    }


def _file_provider_installed() -> bool:
    try:
        from palm.core.registry import provider_registry

        provider_registry.get("file")
        return True
    except Exception:
        return False


def build_resource_preflight(runtime: Any) -> dict[str, Any]:
    """Assemble resource preflight data for doctor reports."""
    repository = getattr(runtime, "repository", None)
    if repository is None:
        return {
            "rest_missing_base_url": [],
            "rest_missing_base_url_count": 0,
            "check_health": {"available": False, "reason": "repository unavailable"},
            "kv": {"resource_count": 0, "backend_resolved": "memory"},
            "file": {"resource_count": 0, "documents_root": None, "writable": None},
            "analytics": {"published_count": 0, "issues": []},
        }

    missing = rest_resources_missing_base_url(repository)
    kv_preflight = build_kv_preflight(runtime, repository)
    file_preflight = build_file_preflight(runtime, repository)
    analytics_preflight = build_analytics_preflight(repository)
    return {
        "rest_missing_base_url": missing,
        "rest_missing_base_url_count": len(missing),
        "check_health": probe_check_health(runtime),
        "kv": kv_preflight,
        "file": file_preflight,
        "analytics": analytics_preflight,
    }


def build_analytics_preflight(repository: Any) -> dict[str, Any]:
    """Published analytics dataset health for doctor."""
    from palm.services.analytics.datasets import READ_ACTION_ALLOWLIST
    from palm.services.analytics.exposure import parse_analytics_exposure

    published = 0
    issues: list[str] = []
    try:
        resources = list(repository.list_resources())
    except Exception:
        return {"published_count": 0, "issues": ["repository list_resources failed"]}

    for res in resources:
        meta = getattr(res, "metadata", None) or {}
        if not isinstance(meta, dict):
            continue
        exp = parse_analytics_exposure(meta)
        if not exp.published:
            continue
        published += 1
        name = getattr(res, "name", None) or getattr(res, "definition_id", "?")
        action = str(getattr(res, "action", "") or "").lower()
        if action and action not in READ_ACTION_ALLOWLIST:
            issues.append(f"published dataset {name!r} has non-read action {action!r}")
        if exp.is_virtual and not exp.source:
            issues.append(f"virtual view {name!r} missing source")
        schema = getattr(res, "output_schema", None)
        if not schema and not exp.fields:
            issues.append(f"published dataset {name!r} has no output_schema or analytics.fields")
    return {"published_count": published, "issues": issues}


def resource_preflight_issues(preflight: dict[str, Any]) -> list[str]:
    """Derive doctor issue strings from a resource preflight payload."""
    issues: list[str] = []
    missing = preflight.get("rest_missing_base_url") or []
    if missing:
        names = ", ".join(str(item.get("name") or "") for item in missing[:5])
        suffix = f" (+{len(missing) - 5} more)" if len(missing) > 5 else ""
        issues.append(f"{len(missing)} REST resource(s) missing base_url: {names}{suffix}")

    file_info = preflight.get("file") or {}
    file_count = int(file_info.get("resource_count") or 0)
    if file_count and file_info.get("writable") is False:
        root = file_info.get("documents_root") or "(unknown)"
        issues.append(f"file documents_root is not writable: {root}")

    if file_count and not file_info.get("provider_installed"):
        issues.append(
            f"{file_count} file resource definition(s) registered but file provider is not installed",
        )

    analytics = preflight.get("analytics") or {}
    for msg in analytics.get("issues") or []:
        issues.append(str(msg))

    return issues


__all__ = [
    "build_analytics_preflight",
    "build_file_preflight",
    "build_kv_preflight",
    "build_resource_preflight",
    "probe_check_health",
    "resolve_documents_root",
    "resource_preflight_issues",
    "rest_resource_has_base_url",
    "rest_resources_missing_base_url",
]