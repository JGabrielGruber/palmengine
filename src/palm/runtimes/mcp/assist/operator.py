"""In-process dispatch of command paths against host services."""

from __future__ import annotations

from typing import Any

from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.services.errors import InstanceNotFoundServiceError

_DELEGATED_PREFIXES = frozenset(
    {"assist", "flows", "processes", "definitions", "design", "system", "providers"},
)


def dispatch_operator_path(
    ctx: Any,
    path: list[str],
    params: dict[str, Any] | None = None,
) -> Any:
    """Dispatch a command path against in-process services."""
    params = params or {}
    if not path:
        raise ValueError("dispatch path must not be empty")
    prefix = path[0]
    if prefix not in _DELEGATED_PREFIXES:
        raise ValueError(f"unsupported dispatch prefix: {prefix!r}")

    if prefix == "assist":
        return ctx.assist.dispatch(path, params)
    if prefix == "flows":
        return ctx.execution.flows.dispatch(path, params)
    if prefix == "processes":
        return ctx.execution.processes.dispatch(path, params)
    if prefix == "definitions":
        return dispatch_definitions(ctx, path, params)
    if prefix == "design":
        return ctx.design.dispatch(path, params)
    if prefix == "system":
        return dispatch_system(ctx, path, params)
    if prefix == "providers":
        return dispatch_providers(ctx, path, params)
    raise ValueError(f"unhandled dispatch prefix: {prefix!r}")


def dispatch_definitions(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    params = params or {}
    body = dict(params.get("body") or params)
    if path == ["definitions", "flows"]:
        return ctx.definitions.list_flows(pattern=params.get("pattern"))
    if len(path) == 2 and path[1] == "flows" and "validate" in params:
        return ctx.definitions.validate_flow(body, runtime=ctx.runtime)
    if len(path) == 2 and path[0] == "definitions" and path[1] == "processes":
        return ctx.definitions.list_processes()
    if len(path) == 2 and path[0] == "definitions" and path[1] == "resources":
        return ctx.definitions.list_resources(provider=params.get("provider"))
    if len(path) == 4 and path[0] == "definitions" and path[1] == "flows" and path[3] == "impact":
        revision = params.get("revision", params.get("target_revision"))
        target_revision = int(revision) if revision is not None else None
        return ctx.definitions.analyze_impact(path[2], target_revision=target_revision)
    if len(path) == 4 and path[0] == "definitions" and path[1] == "instances" and path[3] == "migrate":
        target_revision = params.get("target_revision")
        if target_revision is None:
            raise ValueError("target_revision is required")
        return ctx.definitions.migrate_instance(
            path[2],
            target_revision=int(target_revision),
            dry_run=bool(params.get("dry_run", False)),
        )
    if len(path) == 3 and path[0] == "definitions" and path[1] == "flows":
        revision = params.get("revision")
        return ctx.definitions.get_flow(
            path[2],
            verbose=bool(params.get("verbose", True)),
            revision=int(revision) if revision is not None else None,
        )
    if len(path) == 3 and path[0] == "definitions" and path[1] == "processes":
        return ctx.definitions.get_process(path[2])
    if len(path) == 3 and path[0] == "definitions" and path[1] == "resources":
        return ctx.definitions.get_resource(path[2])
    if len(path) == 3 and path[-1] == "validate" and path[1] == "flows":
        return ctx.definitions.validate_flow(body, runtime=ctx.runtime)
    raise ValueError(f"unrecognized definitions dispatch path: {'/'.join(path)}")


def dispatch_system(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    params = params or {}
    if path == ["system", "doctor"]:
        return ctx.system.doctor(ctx.runtime)
    if path == ["system", "waiting"]:
        from palm.core.orchestration import JobStatus

        limit = params.get("limit", 50)
        try:
            limit_i = int(limit) if limit is not None else 50
        except (TypeError, ValueError):
            limit_i = 50
        rows = ctx.system.list_jobs(
            status=JobStatus.WAITING_FOR_INPUT.value,
            limit=limit_i,
        )
        out: list[dict[str, Any]] = []
        for row in rows or []:
            if hasattr(row, "to_dict"):
                out.append(row.to_dict())
            elif isinstance(row, dict):
                out.append(dict(row))
        return out
    if path == ["system", "jobs"]:
        return ctx.system.list_jobs(
            status=params.get("status"),
            limit=params.get("limit"),
        )
    if len(path) == 2 and path == ["system", "instances"]:
        return ctx.system.list_instances(
            status=params.get("status"),
            flow_name=params.get("flow_name"),
            include_terminal=bool(params.get("include_terminal", True)),
            limit=params.get("limit"),
        )
    if len(path) == 3 and path[0] == "system" and path[1] == "jobs":
        return ctx.system.get_job(path[2])
    if len(path) == 4 and path[0] == "system" and path[1] == "jobs" and path[3] == "context":
        return ctx.system.inspect_job(path[2])
    if len(path) == 3 and path[0] == "system" and path[1] == "instances":
        return ctx.system.inspect_instance(path[2])
    if len(path) == 4 and path[0] == "system" and path[1] == "instances" and path[3] == "tree":
        return build_invoke_tree(ctx.runtime, path[2], base_url=None)
    if len(path) == 4 and path[0] == "system" and path[1] == "instances" and path[3] == "snapshots":
        return ctx.system.list_snapshots(path[2])
    if (
        len(path) == 5
        and path[0] == "system"
        and path[1] == "instances"
        and path[3] == "snapshots"
    ):
        snapshots = ctx.system.list_snapshots(path[2])
        snapshot_id = path[4]
        for index, snap in enumerate(snapshots):
            recorded = getattr(snap, "recorded_at", None) or (
                snap.get("recorded_at") if isinstance(snap, dict) else None
            )
            if str(index) == snapshot_id or str(recorded) == snapshot_id:
                return {"index": index, "snapshot": snap}
        raise InstanceNotFoundServiceError(path[2])
    if len(path) == 4 and path[0] == "system" and path[1] == "jobs" and path[3] == "cancel":
        return ctx.system.cancel_job(path[2])
    raise ValueError(f"unrecognized system dispatch path: {'/'.join(path)}")


def dispatch_providers(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    params = params or {}
    body = dict(params.get("body") or params)
    if len(path) == 4 and path[0] == "providers" and path[3] == "invoke":
        return ctx.execution.providers.invoke(
            path[2],
            provider=path[1],
            action=body.get("action"),
            params=body.get("params"),
            state=body.get("state"),
            resource_id=body.get("resource_id"),
        )
    raise ValueError(f"unrecognized providers dispatch path: {'/'.join(path)}")


__all__ = ["dispatch_operator_path"]
