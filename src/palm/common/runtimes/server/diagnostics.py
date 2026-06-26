"""Server diagnostics — JSON doctor report for REST and operator tooling."""

from __future__ import annotations

from typing import Any

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.transform.registry import transform_registry


def build_doctor_report(runtime: Any) -> dict[str, Any]:
    """Assemble a compact engine health report without Rich CLI output."""
    issues: list[str] = []

    storage = getattr(runtime, "storage", None)
    backend_name = ""
    backend_open = False
    if storage is not None:
        backend_name = storage.backend_name or "(none)"
        backend = storage.backend
        backend_open = backend is not None and backend.is_open

    if not backend_open:
        issues.append(f"storage backend {backend_name!r} is not open")

    orch = getattr(runtime, "orchestration", None)
    jobs = orch.list_jobs() if orch is not None else []
    waiting = sum(1 for job in jobs if job.status.value == "WAITING_FOR_INPUT")

    from palm.common.transforms import autoload as autoload_transforms

    autoload_transforms()

    registries = {
        "patterns": sorted(pattern_registry.names()),
        "providers": sorted(provider_registry.names()),
        "storages": sorted(storage_registry.names()),
        "transforms": sorted(transform_registry.names()),
    }

    resource_count = 0
    repository = getattr(runtime, "repository", None)
    if repository is not None:
        from palm.common.resource.catalog import ResourceCatalog

        resource_count = len(ResourceCatalog(repository).entries())

    return {
        "status": "ok" if not issues else "degraded",
        "version": __version__,
        "runtime": getattr(runtime, "runtime_name", "unknown"),
        "auth_enforce": bool(getattr(runtime, "auth_enforce", False)),
        "storage": {
            "backend": backend_name,
            "open": backend_open,
        },
        "registries": registries,
        "resource_count": resource_count,
        "jobs": {
            "total": len(jobs),
            "waiting_for_input": waiting,
        },
        "issues": issues,
    }


__all__ = ["build_doctor_report"]