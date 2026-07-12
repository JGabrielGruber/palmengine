"""Server diagnostics — JSON doctor report for REST and operator tooling."""

from __future__ import annotations

from typing import Any

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.transform.registry import transform_registry


def build_doctor_report(
    runtime: Any,
    *,
    control_plane: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    resource_preflight: dict[str, Any] = {}
    repository = getattr(runtime, "repository", None)
    if repository is not None:
        from palm.common.resource.catalog import ResourceCatalog
        from palm.common.resource.preflight import build_resource_preflight

        resource_count = len(ResourceCatalog(repository).entries())
        resource_preflight = build_resource_preflight(runtime)
        from palm.common.resource.preflight import resource_preflight_issues

        issues.extend(resource_preflight_issues(resource_preflight))

    cp = control_plane if isinstance(control_plane, dict) else {}
    if not cp:
        # ServerRuntime.host is bind address; prefer host_bridge / application_host
        for attr in ("application_host", "host_bridge", "_host_bridge", "host"):
            host = getattr(runtime, attr, None)
            if host is not None and hasattr(host, "control_plane_status"):
                try:
                    cp = dict(host.control_plane_status() or {})
                except Exception:
                    cp = {}
                break

    # Soft issues from control plane lag / backlog
    if cp:
        work_pending = int(cp.get("work_pending") or 0)
        if work_pending > 50:
            issues.append(f"work_pending={work_pending} (WorkIntent backlog)")
        journal = cp.get("journal") if isinstance(cp.get("journal"), dict) else {}
        consumers = journal.get("consumers") if isinstance(journal, dict) else {}
        if isinstance(consumers, dict):
            for name, row in consumers.items():
                if not isinstance(row, dict):
                    continue
                lag = int(row.get("lag") or 0)
                if lag > 100:
                    issues.append(f"journal consumer {name!r} lag={lag}")

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
        "resource_preflight": resource_preflight,
        "control_plane": cp or {
            "work_pending": 0,
            "work_drain_running": False,
            "outbox_pending": 0,
            "journal": {},
        },
        "jobs": {
            "total": len(jobs),
            "waiting_for_input": waiting,
        },
        "issues": issues,
    }


__all__ = ["build_doctor_report"]
