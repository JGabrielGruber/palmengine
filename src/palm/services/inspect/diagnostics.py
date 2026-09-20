"""Inspect anatomy packaging for the legacy doctor verb.

0.61.6 / OD-001: this module builds **anatomy packaging** only (storage,
registries, job counts, host control_plane residual). It does **not**
invent living seat law. Living eyes live in ``palm.system.vitality`` and
are presented via ``InspectService.top`` / ``.vitality``. Prefer those
paths; call this only as residual packaging consumed by
:meth:`InspectService.doctor` / CLI health dumps.

0.71.21: home is inspect (not ``palm.kits.server``) so ApplicationHost does
not pull the server kit for doctor anatomy.
"""

from __future__ import annotations

from typing import Any

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.transform.registry import transform_registry
from palm.system.subsystems.planes.wait.plane import WaitPlaneService
from palm.system.subsystems.planes.wait.present import waiting_on_from_job

# OD-001 residual marker — not living seat law.
_ANATOMY_ROLE = "anatomy_packaging"
_ANATOMY_NOTE = (
    "Anatomy packaging residual (OD-001). Living eyes: InspectService.top / "
    "vitality → palm.system.vitality. Do not treat this bag as seat law."
)


def build_doctor_report(
    runtime: Any,
    *,
    control_plane: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble anatomy packaging (storage, registries, jobs) — not vitality.

    Residual for the legacy ``doctor`` verb. Does not invent seat reports or
    projection summary. Prefer :meth:`~palm.services.inspect.InspectService.top`.
    """
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

    execution = getattr(runtime, "execution", None)
    if execution is not None and hasattr(execution, "list_jobs"):
        jobs = execution.list_jobs()
    else:
        orch = getattr(runtime, "orchestration", None)
        jobs = orch.list_jobs() if orch is not None else []
    waiting = sum(1 for job in jobs if job.status.value == "WAITING_FOR_INPUT")
    plane = getattr(runtime, "wait_plane", None)
    if isinstance(plane, WaitPlaneService):
        reactive = plane.doctor_snapshot(jobs)
        open_wait_owners = int(reactive.get("open_wait_owners") or 0)
        open_wait_interests = int(reactive.get("open_wait_interests") or 0)
        wait_kind_counts = dict(reactive.get("wait_kinds") or {})
        wait_matcher_wired = bool(reactive.get("wait_matcher_wired"))
    else:
        open_wait_owners = 0
        open_wait_interests = 0
        wait_kind_counts: dict[str, int] = {}
        for job in jobs:
            rows = waiting_on_from_job(job)
            if not rows:
                continue
            open_wait_owners += 1
            open_wait_interests += len(rows)
            for row in rows:
                kind = str(row.get("kind") or "unknown")
                wait_kind_counts[kind] = wait_kind_counts.get(kind, 0) + 1
        wait_matcher_wired = getattr(runtime, "wait_matcher", None) is not None
        reactive = {
            "wait_matcher_wired": wait_matcher_wired,
            "open_wait_owners": open_wait_owners,
            "open_wait_interests": open_wait_interests,
            "wait_kinds": wait_kind_counts,
            "verbs": ["start", "continue"],
            "note": (
                "start = trigger → WorkIntent; continue = WaitPlaneService " "(VISION-0.55.10)"
            ),
        }

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
        # ServerRuntime.host is bind address; prefer host packaging residual (CS-002).
        for attr in ("application_host", "host_bridge", "_host_bridge", "host"):
            host = getattr(runtime, attr, None)
            if host is None:
                continue
            try:
                if hasattr(host, "packaging_status"):
                    cp = dict(host.packaging_status() or {})
                elif hasattr(host, "control_plane_status"):
                    cp = dict(host.control_plane_status() or {})
            except Exception:
                cp = {}
            if cp:
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

    from palm.system.subsystems.planes.workload.bootstrap import workload_doctor_section

    try:
        workloads = workload_doctor_section(runtime)
        issues.extend(str(i) for i in (workloads.get("issues") or []))
    except Exception as exc:
        workloads = {"error": f"workload doctor failed: {exc}"}

    # Also expose workload runtimes in registries snapshot
    try:
        from palm.core.workload.registry import workload_runtime_registry

        registries["workload_runtimes"] = sorted(workload_runtime_registry.names())
    except Exception:
        registries["workload_runtimes"] = []

    return {
        "role": _ANATOMY_ROLE,
        "note": _ANATOMY_NOTE,
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
        "workloads": workloads,
        # control_plane from host is CS-002 residual — packaging, not living law.
        "control_plane": cp
        or {
            "work_pending": 0,
            "start_plane_running": False,
            "outbox_pending": 0,
            "journal": {},
        },
        "jobs": {
            "total": len(jobs),
            "waiting_for_input": waiting,
            "open_wait_owners": open_wait_owners,
            "open_wait_interests": open_wait_interests,
            "wait_kinds": wait_kind_counts,
        },
        # Plane doctor_snapshot residual — transitional (seat report later).
        "reactive_interests": reactive,
        "issues": issues,
    }


__all__ = ["build_doctor_report"]
