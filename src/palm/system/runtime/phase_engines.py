"""
System start phase: engine init (system.engines.init).

Subject: system instance shell engines (context, event, resource, workload, auth).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.common.resource import resource_definition_resolver
from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition
from palm.system.boot.shell import resolve_shell
from palm.system.bound import BoundDrivers
from palm.system.runtime.hooks import authenticate_runtime
from palm.system.subsystems.planes.workload.bootstrap import initialize_workload_engine


def init_system_engines(
    shell: Any,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Initialize core engines on *shell*; return seats for BootContext."""
    opts = dict(options or {})
    shell.context.initialize()
    shell.event.initialize()

    resource_options: dict[str, Any] = {
        "event_engine": shell.event,
        "definition_resolver": resource_definition_resolver(shell.repository),
    }
    cache_options = opts.get("resource_cache")
    if cache_options is not None:
        resource_options["resource_cache"] = cache_options
    shell.resource.initialize(**resource_options)

    def _publish_workload(event_type: str, payload: dict[str, Any]) -> None:
        shell.event.emit(event_type, **payload)

    drivers = opts.get("drivers")
    slot = drivers.workload_runtime if isinstance(drivers, BoundDrivers) else None
    initialize_workload_engine(
        shell.workload,
        host_enabled=bool(opts.get("workload_host_enabled", False)),
        work_root=opts.get("workload_work_root") or opts.get("data_dir"),
        default_runtime=None if slot is None else slot.default,
        runtime_names=() if slot is None else slot.names,
        publish_event=_publish_workload,
    )

    shell.auth.initialize()
    authenticate_runtime(shell.auth, opts.get("credentials"))

    return {
        "context_engine": shell.context,
        "event": shell.event,
        "resource": shell.resource,
        "workload": shell.workload,
        "auth": shell.auth,
    }


def run(ctx: BootContext, options: Mapping[str, Any]) -> None:
    seats = init_system_engines(resolve_shell(ctx), options)
    ctx.publish(**seats)


DEFINITION = PhaseDefinition(
    id="system.engines.init",
    run=run,
    description="context, event, resource, workload, auth",
)

__all__ = ["DEFINITION", "init_system_engines", "run"]
