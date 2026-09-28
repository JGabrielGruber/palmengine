"""Wire WorkloadEngine with bound runner instances.

The engine binds the runtime names the caller passes. It does not import
runner packages and it does not choose a default name. ``host`` starts
disabled unless ``host_enabled`` is set.
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
    names: tuple[str, ...],
    host_enabled: bool = False,
    work_root: Path | str | None = None,
) -> dict[str, WorkloadRuntime]:
    """Construct live runtime instances for the names the bundle registered.

    Does not import runner packages and does not add a name of its own.
    """
    from palm.core.workload.registry import workload_runtime_registry

    missing = [name for name in names if name not in workload_runtime_registry.names()]
    if missing:
        listed = ", ".join(missing)
        raise RuntimeError(f"workload runtime not registered: {listed}")
    return {
        name: workload_runtime_registry.get(name).bind(
            host_enabled=host_enabled,
            work_root=work_root,
        )
        for name in names
    }


def initialize_workload_engine(
    engine: WorkloadEngine,
    *,
    host_enabled: bool = False,
    work_root: Path | str | None = None,
    default_runtime: str | None = None,
    runtime_names: tuple[str, ...] = (),
    publish_event: EventPublisher | None = None,
) -> WorkloadEngine:
    """Initialize the engine with the named runtimes. No default name is added."""
    runtimes = build_bound_runtimes(
        names=runtime_names,
        host_enabled=host_enabled,
        work_root=work_root,
    )
    engine.initialize(
        runtimes=runtimes,
        default_runtime=default_runtime,
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
