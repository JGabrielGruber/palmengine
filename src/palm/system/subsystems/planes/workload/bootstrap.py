"""Wire WorkloadEngine with bound runner instances.

**local** is always on (trusted Palm process runner).
**host** is opt-in (PALM_WORKLOAD_HOST_ENABLED).
**neonroot** is hermetic when CLI present.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from palm.core.workload.engine import WorkloadEngine
from palm.core.workload.protocol import WorkloadRuntime

EventPublisher = Callable[[str, dict[str, Any]], None]


def build_bound_runtimes(
    *,
    host_enabled: bool = False,
    work_root: Path | str | None = None,
) -> dict[str, WorkloadRuntime]:
    """Construct live runtime instances for engine.initialize(runtimes=…)."""
    from palm.runners import autoload as autoload_runners
    from palm.runners.host.runtime import HostWorkloadRuntime
    from palm.runners.local.runtime import LocalWorkloadRuntime
    from palm.runners.neonroot.runtime import NeonrootWorkloadRuntime

    autoload_runners()

    # Prefer a dedicated workloads subdir under data_dir when provided
    local_root = None
    if work_root is not None:
        local_root = Path(work_root) / "workloads"

    return {
        "local": LocalWorkloadRuntime(work_root=local_root or work_root),
        "host": HostWorkloadRuntime(enabled=host_enabled, work_root=work_root),
        "neonroot": NeonrootWorkloadRuntime(),
    }


def initialize_workload_engine(
    engine: WorkloadEngine,
    *,
    host_enabled: bool = False,
    work_root: Path | str | None = None,
    default_runtime: str | None = None,
    publish_event: EventPublisher | None = None,
) -> WorkloadEngine:
    """Initialize engine; default_runtime falls back to **local** (always on)."""
    runtimes = build_bound_runtimes(host_enabled=host_enabled, work_root=work_root)
    engine.initialize(
        runtimes=runtimes,
        default_runtime=default_runtime or "local",
        publish_event=publish_event,
    )
    return engine


def workload_doctor_section(runtime: Any = None) -> dict[str, Any]:
    """Aggregate workload plane doctor view via engine.doctor() when possible."""
    from palm.core.workload.registry import workload_runtime_registry
    from palm.runners import autoload as autoload_runners

    autoload_runners()

    registered = sorted(workload_runtime_registry.names())
    engine = getattr(runtime, "workload", None) if runtime is not None else None
    if engine is not None and getattr(engine, "is_initialized", False):
        snap = engine.doctor()
        return {
            **snap,
            "registered_runtimes": registered,
            "note": snap.get("note")
            or (
                "local = always-on Palm process runner; host = opt-in unsafe; "
                "neonroot = hermetic external CLI"
            ),
        }

    return {
        "engine_initialized": False,
        "registered_runtimes": registered,
        "runtimes": [],
        "issues": ["WorkloadEngine not bound on runtime"],
        "note": "local / host / neonroot WorkloadRuntimes",
    }


__all__ = [
    "build_bound_runtimes",
    "initialize_workload_engine",
    "workload_doctor_section",
]
