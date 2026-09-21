"""Wire WorkloadEngine with bound runner instances.

The engine binds runners the composition record already installed.
``local`` is the trusted default. ``host`` starts disabled unless
``host_enabled`` is set. ``neonroot`` binds when that package was installed.
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
    """Construct live runtime instances for engine.initialize(runtimes=…).

    Walks the workload runtime registry. Does not import runner packages.
    """
    from palm.core.workload.registry import workload_runtime_registry

    return {
        name: workload_runtime_registry.get(name).bind(
            host_enabled=host_enabled,
            work_root=work_root,
        )
        for name in workload_runtime_registry.names()
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
        "note": "installed WorkloadRuntimes",
    }


__all__ = [
    "build_bound_runtimes",
    "initialize_workload_engine",
    "workload_doctor_section",
]
