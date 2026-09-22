"""In-process dispatch of command paths against host services."""

from __future__ import annotations

from typing import Any

from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.services.errors import InstanceNotFoundServiceError

_DELEGATED_PREFIXES = frozenset(
    {
        "assist",
        "flows",
        "processes",
        "definitions",
        "design",
        "system",
        "inspect",  # 0.61.5 product door alias for operate paths
        "providers",
        "workloads",
    },
)


def dispatch_operator_path(
    ctx: Any,
    path: list[str],
    params: dict[str, Any] | None = None,
) -> Any:
    """Dispatch a command path against in-process services."""
    params = dict(params or {})
    if not path:
        raise ValueError("dispatch path must not be empty")
    path = list(path)
    # 0.58.8 — system session subject may appear where product expects instance id
    path, params = rewrite_system_session_continue(ctx, path, params)
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
    if prefix in ("system", "inspect"):
        return dispatch_system(ctx, path, params)
    if prefix == "providers":
        return dispatch_providers(ctx, path, params)
    if prefix == "workloads":
        return dispatch_workloads(ctx, path, params)
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


def _resolve_session_service(ctx: Any) -> Any | None:
    """Product SessionService — kit single door (0.58.17)."""
    from plugins.kits.server.middleware import resolve_session_service

    return resolve_session_service(ctx)


def rewrite_system_session_continue(
    ctx: Any,
    path: list[str],
    params: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    """Map system session ids to product continue handles (attach list).

    **0.58.9 law:** ``session_id`` is always the system subject. Product path
    segments still expect an **instance** id (SI-001/005). When a path or
    param carries ``sess-…`` where product needs an instance, resolve via
    product :class:`~palm.services.session.SessionService`
    ``resolve_continue_instance`` (active → waiting → last). Does **not**
    invent resume. Does **not** write the instance back into ``session_id``.

    **0.58.11 SI-015:** when a system ``session_id`` is bound and the path is a
    product continue/inspect under that subject, the continue ``instance_id``
    must be on the session attach list
    (:meth:`~palm.services.session.SessionService.require_owned_instance`).

    **0.58.15 strict attribution:** continue paths without a system session
    resolve the owner from the plane; orphan / bare instances raise
    :class:`~palm.system.subsystems.planes.session.SessionAttributionError`.

    **0.58.17:** product door only — no raw ``session_plane`` fallback.
    """
    from palm.system.subsystems.planes.session import looks_like_system_session_id

    product = _resolve_session_service(ctx)
    if product is None:
        return path, params

    out_params = dict(params)
    out_path = list(path)

    def _resolve(sid: str) -> str | None:
        try:
            resolved = product.resolve_continue_instance(sid)
            return str(resolved) if resolved else None
        except Exception:
            return None

    def _apply_instance(inst: str, system_sid: str) -> None:
        out_params["session_id"] = system_sid
        out_params["instance_id"] = inst

    # Path: assist/instance/{id}/… or flows/{flow}/instance/{id}/…
    # (legacy segment ``session`` still accepted — 0.58.19 soft land)
    if (
        len(out_path) >= 3
        and out_path[0] == "assist"
        and out_path[1] in {"instance", "session"}
    ):
        raw = out_path[2]
        if looks_like_system_session_id(raw):
            inst = _resolve(str(raw))
            if inst:
                out_path[1] = "instance"
                out_path[2] = inst
                _apply_instance(inst, str(raw))
    elif (
        len(out_path) >= 4
        and out_path[0] == "flows"
        and out_path[2] in {"instance", "session"}
    ):
        raw = out_path[3]
        if looks_like_system_session_id(raw):
            inst = _resolve(str(raw))
            if inst:
                out_path[2] = "instance"
                out_path[3] = inst
                _apply_instance(inst, str(raw))

    # Explicit product instance in the path is the continue target (do not
    # replace it with resolve_continue_instance of the bound session — that
    # would hide SI-015 foreign-instance attempts).
    path_inst = _path_continue_instance(out_path)
    if path_inst and not looks_like_system_session_id(path_inst):
        out_params["instance_id"] = path_inst

    # Params: session_id is system; instance_id is continue (resolve if missing).
    system_sid = out_params.get("session_id")
    inst_param = out_params.get("instance_id")
    if looks_like_system_session_id(system_sid):
        if not inst_param or looks_like_system_session_id(inst_param):
            inst = _resolve(str(system_sid))
            if inst:
                out_params["instance_id"] = inst
        # Keep session_id as system — never overwrite with instance.
    elif looks_like_system_session_id(inst_param) and not looks_like_system_session_id(
        system_sid or ""
    ):
        # Misplaced system id in instance_id — correct and resolve.
        system_sid = str(inst_param)
        out_params["session_id"] = system_sid
        inst = _resolve(system_sid)
        if inst:
            out_params["instance_id"] = inst

    # SI-015 + 0.58.15: continue attribution via product door only
    _gate_continue_owner(product, out_path, out_params)

    return out_path, out_params


def _path_continue_instance(path: list[str]) -> str | None:
    """Extract product instance id from assist/flows continue paths."""
    if len(path) >= 3 and path[0] == "assist" and path[1] in {"instance", "session"}:
        return str(path[2]) if path[2] else None
    if len(path) >= 4 and path[0] == "flows" and path[2] in {"instance", "session"}:
        return str(path[3]) if path[3] else None
    return None


def _is_session_continue_path(path: list[str]) -> bool:
    """True for product paths that drive or inspect a flow/assist instance."""
    if len(path) >= 3 and path[0] == "assist" and path[1] in {"instance", "session"}:
        return True
    if len(path) >= 4 and path[0] == "flows" and path[2] in {"instance", "session"}:
        return True
    return False


def _gate_continue_owner(
    door: Any,
    path: list[str],
    params: dict[str, Any],
) -> None:
    """Continue attribution via product SessionService (0.58.11 / 0.58.15 / 0.58.17)."""
    from palm.system.subsystems.planes.session import looks_like_system_session_id

    if not _is_session_continue_path(path):
        return
    # Prefer path instance (explicit handle) over param (may be plane focus).
    path_inst = _path_continue_instance(path)
    param_inst = params.get("instance_id")
    if path_inst and not looks_like_system_session_id(path_inst):
        candidate = path_inst
    elif param_inst and not looks_like_system_session_id(param_inst):
        candidate = param_inst
    else:
        return

    if hasattr(door, "gate_bound_session_owns"):
        # Operator rewrite: refuse bare orphans (do not defer to 404).
        door.gate_bound_session_owns(
            str(candidate).strip(), params, allow_unknown=False
        )
        return
    # Product door without gate helper — still require ownership when system bound
    system_sid = params.get("session_id")
    if looks_like_system_session_id(system_sid) and hasattr(
        door, "require_owned_instance"
    ):
        door.require_owned_instance(str(system_sid).strip(), str(candidate).strip())


def dispatch_system(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    """Operate door for inspect product (paths may still say ``system/*``)."""
    params = params or {}
    # Normalize inspect/* → system/* for residual wire matching (SD-007 residual).
    if path and path[0] == "inspect":
        path = ["system", *path[1:]]
    door = getattr(ctx, "inspect", None) or ctx.system
    if path == ["system", "doctor"]:
        return door.doctor(ctx.runtime)
    if path == ["system", "top"]:
        return door.top(ctx.runtime)
    if path == ["system", "vitality"]:
        return door.vitality(ctx.runtime)
    # 0.58.8 / 0.58.12 / 0.58.17 / 0.58.18 — session journey + operate (product door)
    if len(path) >= 3 and path[0] == "system" and path[1] == "session":
        door = _resolve_session_service(ctx)
        if door is None:
            raise ValueError(
                "SessionService not available (0.58.17 product door required)"
            )
        sid = path[2]
        if len(path) == 3:
            return door.inspect(sid)
        if len(path) == 4 and path[3] == "view":
            return door.surface_view(sid)
        if len(path) == 4 and path[3] == "waiting":
            return door.list_waiting(sid)
        if len(path) == 4 and path[3] == "instances":
            return door.list_instances(sid)
        if len(path) == 4 and path[3] == "focus":
            # params.instance_id required to set focus
            iid = params.get("instance_id") or params.get("active_instance_id")
            if not iid:
                raise ValueError(
                    "system/session/{id}/focus requires params.instance_id"
                )
            bound = door.focus(sid, str(iid))
            return {
                "kind": "session_focus",
                "session_id": sid,
                "active_instance_id": bound.instance_id,
                "bound_surface": bound.to_dict(),
            }
        if len(path) == 5 and path[3] == "focus" and path[4] == "clear":
            bound = door.clear_focus(sid)
            return {
                "kind": "session_focus_clear",
                "session_id": sid,
                "active_instance_id": bound.instance_id,
                "bound_surface": bound.to_dict(),
            }
        if len(path) == 4 and path[3] == "cancel":
            return door.cancel_owned(
                sid,
                instance_id=params.get("instance_id"),
                job_id=params.get("job_id"),
            )
        if len(path) == 5 and path[3] == "cancel" and path[4] == "all":
            return door.cancel_all_owned(
                sid,
                only_waiting=bool(params.get("only_waiting", False)),
            )
        raise ValueError(f"unrecognized system session path: {'/'.join(path)}")
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


def dispatch_workloads(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    """Assist/MCP path dispatch for execution.workloads (0.56 small surface)."""
    params = params or {}
    body = dict(params.get("body") or params)
    svc = ctx.execution.workloads

    # workloads / workloads/start
    if path in (["workloads"], ["workloads", "start"]) and (
        "spec" in body or "spec" in params
    ):
        return svc.start(
            body.get("spec") or params.get("spec"),
            owner=body.get("owner") or params.get("owner"),
            workload_id=body.get("workload_id") or params.get("workload_id"),
            idempotency_key=body.get("idempotency_key") or params.get("idempotency_key"),
            host_id=body.get("host_id") or params.get("host_id"),
            runtime_name=body.get("runtime_name") or params.get("runtime_name"),
        )
    if path == ["workloads"] or path == ["workloads", "list"]:
        return {
            "workloads": svc.list(
                job_id=params.get("job_id"),
                instance_id=params.get("instance_id"),
                session_id=params.get("session_id"),
                status=params.get("status"),
                runtime=params.get("runtime"),
                runtime_name=params.get("runtime_name"),
            )
        }
    if path == ["workloads", "runtimes"]:
        return {"runtimes": svc.runtimes(runtime_name=params.get("runtime_name"))}
    if path == ["workloads", "hosts"]:
        return {"hosts": svc.hosts(runtime_name=params.get("runtime_name"))}
    if path == ["workloads", "doctor"]:
        return svc.doctor(runtime_name=params.get("runtime_name"))
    if len(path) == 2 and path[0] == "workloads":
        return svc.get(
            path[1],
            refresh=bool(params.get("refresh", False)),
            runtime_name=params.get("runtime_name"),
        )
    if len(path) == 3 and path[0] == "workloads" and path[2] == "stop":
        return svc.stop(path[1], runtime_name=body.get("runtime_name") or params.get("runtime_name"))
    if len(path) == 3 and path[0] == "workloads" and path[2] == "exec":
        command = body.get("command") or params.get("command")
        if not command:
            raise ValueError("command (argv list) is required")
        return svc.exec(
            path[1],
            command,
            timeout_s=body.get("timeout_s") or params.get("timeout_s"),
            env=body.get("env") or params.get("env"),
            runtime_name=body.get("runtime_name") or params.get("runtime_name"),
        )
    raise ValueError(f"unrecognized workloads dispatch path: {'/'.join(path)}")


__all__ = ["dispatch_operator_path"]
