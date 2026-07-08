"""Parametric operator dispatch — assist proxy over service command paths."""

from __future__ import annotations

from typing import Any

from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    normalize_view_format,
)
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.runtimes.mcp.assist.routes_catalog import build_assist_routes_catalog
from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.runtimes.mcp.flows.views import flatten_session_view, submission_view
from palm.services.assist.registry import resolve_mcp_alias
from palm.services.design.registry import resolve_design_mcp_alias
from palm.services.design.views import (
    build_design_impact_assistant_view,
    build_design_validate_assistant_view,
)
from palm.services.assist.views import resolve_view_format

_DELEGATED_PREFIXES = frozenset(
    {"assist", "flows", "processes", "definitions", "design", "system", "providers"},
)

_DEFAULT_ASSIST_ALIAS = "operator-entry/start"


def _clean_dispatch_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_assist_dispatch_args(
    *,
    path: list[str] | None = None,
    alias: str | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[list[str] | None, str | None, dict[str, Any], bool]:
    """Coerce weak-LLM tool payloads and apply human-first defaults.

    Returns ``(path, alias, params, used_default_entry)``.
    """
    params = dict(params or {})
    used_default_entry = False

    alias = _clean_dispatch_str(alias)
    if alias is None:
        alias = _clean_dispatch_str(params.pop("alias", None))

    if path is not None:
        cleaned = [_clean_dispatch_str(segment) for segment in path]
        path = [segment for segment in cleaned if segment] or None
    if path is None:
        nested = params.pop("path", None)
        if isinstance(nested, list):
            cleaned = [_clean_dispatch_str(segment) for segment in nested]
            path = [segment for segment in cleaned if segment] or None

    if not alias and not path:
        session_id = _clean_dispatch_str(params.get("session_id")) or _clean_dispatch_str(
            params.get("instance_id")
        )
        flow_id = _clean_dispatch_str(params.get("flow_id"))
        has_value = "value" in params or "input" in params
        collection_action = params.get("collection_action")
        edit = params.get("edit")
        if session_id and flow_id and (
            has_value or collection_action is not None or isinstance(edit, dict)
        ):
            path = ["flows", flow_id, "session", session_id, "input"]
            if collection_action is not None and "input" not in params:
                action_text = _clean_dispatch_str(collection_action) or str(collection_action)
                params["input"] = action_text
        elif session_id and has_value:
            path = ["assist", "session", session_id, "input"]
        elif session_id and flow_id:
            path = ["flows", flow_id, "session", session_id]
        elif session_id:
            path = ["assist", "session", session_id]
        elif flow_id:
            # 0.30.6 — palm_assist(params={flow_id}) starts the flow (one call)
            path = ["flows", flow_id, "create"]
        else:
            scenario_id = _clean_dispatch_str(params.get("scenario_id"))
            if scenario_id:
                alias = f"{scenario_id}/start"
            elif _looks_like_design_publish_body(params):
                # 0.30.5 — one-shot design publish via palm_assist(params={body})
                kind = _clean_dispatch_str(params.get("kind")) or "flow"
                if kind in {"resource", "publish-resource"}:
                    alias = "design/publish-resource"
                else:
                    alias = "design/publish"

    if not alias and not path:
        alias = _DEFAULT_ASSIST_ALIAS
        used_default_entry = True

    return path, alias, params, used_default_entry


def _looks_like_design_publish_body(params: dict[str, Any]) -> bool:
    """True when params carry a flow/resource definition body for one-shot publish."""
    body = params.get("body")
    if not isinstance(body, dict) or not body:
        # Allow top-level name/pattern without nested body (weak-LLM)
        if params.get("name") and (params.get("pattern") or params.get("options")):
            return True
        if params.get("name") and params.get("provider"):
            return True
        return False
    if body.get("name") or body.get("pattern") or body.get("options"):
        return True
    if body.get("provider") or body.get("resource_id"):
        return True
    return False


def resolve_dispatch_path(
    *,
    path: list[str] | None = None,
    alias: str | None = None,
    params: dict[str, Any] | None = None,
) -> list[str]:
    """Resolve alias or explicit path into a concrete command path."""
    path, alias, params, _ = normalize_assist_dispatch_args(
        path=path,
        alias=alias,
        params=params,
    )
    if alias:
        resolved = resolve_mcp_alias(alias, params=params)
        if resolved is None:
            resolved = resolve_design_mcp_alias(alias, params=params)
        if resolved is None:
            if alias == _DEFAULT_ASSIST_ALIAS:
                return ["assist", "scenarios"]
            raise ValueError(f"unknown MCP alias: {alias!r}")
        return list(resolved)
    if path:
        return [str(segment) for segment in path]
    return ["assist", "scenarios"]


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
        return _dispatch_definitions(ctx, path, params)

    if prefix == "design":
        return ctx.design.dispatch(path, params)

    if prefix == "system":
        return _dispatch_system(ctx, path, params)

    if prefix == "providers":
        return _dispatch_providers(ctx, path, params)

    raise ValueError(f"unhandled dispatch prefix: {prefix!r}")


def _coerce_dispatch_result(result: Any) -> Any:
    """Normalize dataclass session views before compact branching."""
    if isinstance(result, dict):
        return result
    if hasattr(result, "session_id") and hasattr(result, "to_dict"):
        return result.to_dict()
    return result


def resolve_dispatch_format(
    path: list[str],
    *,
    params: dict[str, Any] | None = None,
    tool_format: str | None = None,
) -> str:
    """Resolve view format for palm_assist (human-first).

    Assist + design always prefer assistant. Flows paths (create/session)
    honor ``tool_format`` from palm_assist (default assistant) so weak LLMs
    get questions/choices without remembering format=assistant each call.
    Direct palm_flows_* tools do not use this helper and stay powertool-default.
    """
    prefix = path[0] if path else ""
    merged = dict(params or {})
    if tool_format is not None and "format" not in merged:
        merged["format"] = tool_format
    if prefix in {"assist", "design", "flows"}:
        return resolve_view_format(merged, default="assistant")
    if "format" in merged:
        return resolve_view_format(merged, default="powertool")
    return "powertool"


def shape_dispatch_result(
    path: list[str],
    result: Any,
    *,
    format: str | None = None,
    params: dict[str, Any] | None = None,
    tool_format: str | None = None,
    invoke_tree: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shape domain dispatch results for MCP operator consumers."""
    fmt = normalize_view_format(
        format or resolve_dispatch_format(path, params=params, tool_format=tool_format)
    )
    payload: dict[str, Any] = {"path": path}
    raw = result
    result = _coerce_dispatch_result(result)
    if not isinstance(result, dict):
        payload["result"] = result
        return payload

    if "handoff" in result:
        payload.update(result)
        return payload

    prefix = path[0] if path else ""

    if prefix == "assist" and "session_id" in result:
        if fmt == "assistant" or result.get("question"):
            payload.update(result)
            return payload
        if result.get("detail"):
            flat = _assist_session_flat(result)
            shaped = build_operator_view(
                "powertool",
                flat_view=flat,
                context=_operator_context_from_assist(result),
            )
            payload.update(shaped)
            for key in ("operator_hint", "compose_status", "handoff_ready", "scenario_id", "next_commands"):
                if result.get(key) is not None:
                    payload[key] = result[key]
            return payload
        if "scenario_id" in result and "question" not in result:
            payload.update(submission_view(result))
            return payload

    if prefix == "flows" and _looks_like_session(path, result):
        flat = flatten_session_view(raw)
        _ensure_flow_session_flat(flat, path)
        payload.update(
            shape_flow_session_view(
                flat,
                format=fmt,
                session_id=flat.get("instance_id") or flat.get("session_id"),
                flow_id=flat.get("flow_name") or flat.get("flow"),
                path=path,
                invoke_tree=invoke_tree,
            )
        )
        return payload

    if prefix == "flows" and path[-1:] == ["create"]:
        if fmt == "assistant":
            payload.update(_shape_flow_create_assistant(result, path=path))
        else:
            payload.update(submission_view(result))
        return payload

    if prefix == "system" and _looks_like_job_context(result):
        payload.update(
            build_operator_view(
                fmt,
                flat_view=result,
                context=OperatorViewContext(path=list(path)),
            )
        )
        return payload

    if prefix == "system" and path[-1:] == ["doctor"]:
        payload["doctor"] = result
        return payload

    if prefix == "design" and fmt == "assistant":
        proposal_id = _design_proposal_id_from_path(path, result)
        if proposal_id and path[-1:] == ["validate"] and isinstance(result, dict):
            payload.update(build_design_validate_assistant_view(proposal_id, result))
            return payload
        if proposal_id and path[-1:] == ["impact"] and isinstance(result, dict):
            valid = bool((result.get("mutation") or {}).get("mutations_allowed"))
            payload.update(build_design_impact_assistant_view(proposal_id, result, valid=valid))
            return payload
        # 0.30.5 — compact one-shot publish / publish-resource results
        if path[-1:] in (["publish"], ["publish-resource"]) and isinstance(result, dict):
            payload.update(_shape_design_publish_assistant(result))
            return payload

    payload.update(result)
    return payload


def _shape_design_publish_assistant(result: dict[str, Any]) -> dict[str, Any]:
    """Human-first envelope for publish_flow / publish_resource responses."""
    status = result.get("status")
    shaped: dict[str, Any] = {
        "status": status,
        "stage": result.get("stage"),
        "hint": result.get("hint"),
        "actions": result.get("actions") or [],
    }
    if result.get("proposal_id") is not None:
        shaped["proposal_id"] = result["proposal_id"]
    if result.get("flow_id") is not None:
        shaped["flow_id"] = result["flow_id"]
    if result.get("revision") is not None:
        shaped["revision"] = result["revision"]
    if result.get("resource_ref") is not None:
        shaped["resource_ref"] = result["resource_ref"]
    if status == "committed":
        shaped["question"] = (
            f"Published {result.get('flow_id') or result.get('resource_ref')!r}. "
            "Use actions to run or inspect."
        )
    elif status == "blocked":
        shaped["question"] = "Publish blocked by validation — fix body and retry."
        if result.get("validation") is not None:
            shaped["validation"] = result["validation"]
    else:
        shaped["result"] = result
    return shaped


def _shape_flow_create_assistant(
    result: dict[str, Any],
    *,
    path: list[str],
) -> dict[str, Any]:
    """Minimal create envelope when first-turn re-inspect is unavailable."""
    session_id = result.get("session_id") or result.get("instance_id")
    flow_id = result.get("flow_id") or result.get("flow")
    if flow_id is None and len(path) >= 2 and path[0] == "flows":
        flow_id = path[1]
    shaped = submission_view(result)
    shaped["status"] = _human_status(shaped.get("status"))
    shaped["question"] = (
        f"Session started for {flow_id!r}. Reply with your next answer via palm_assist."
    )
    shaped["hint"] = (
        f'palm_assist(params={{"session_id": "{session_id}", "flow_id": "{flow_id}", "value": "…"}})'
    )
    if session_id and flow_id:
        shaped["actions"] = [
            {
                "label": "Continue session",
                "alias": "flows/session-input",
                "params": {"session_id": session_id, "flow_id": flow_id},
            },
            {
                "label": "Inspect session",
                "alias": "flows/session",
                "params": {"session_id": session_id, "flow_id": flow_id, "format": "assistant"},
            },
        ]
    return shaped


def _human_status(raw: object | None) -> str:
    if raw is None:
        return "waiting"
    text = str(raw).upper()
    if text == "WAITING_FOR_INPUT":
        return "waiting"
    if text in {"SUCCEEDED", "SUCCESS"}:
        return "complete"
    if text in {"FAILED", "CANCELLED"}:
        return "failed"
    if text == "RUNNING":
        return "running"
    return str(raw).lower()


def compact_dispatch_result(
    path: list[str],
    result: Any,
    *,
    format: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Alias for :func:`shape_dispatch_result` defaulting non-assist paths to powertool."""
    resolved = format or resolve_dispatch_format(path, params=params, tool_format=None)
    return shape_dispatch_result(path, result, format=resolved, params=params)


def assist_routes_payload() -> dict[str, Any]:
    return build_assist_routes_catalog()


def _assist_session_flat(result: dict[str, Any]) -> dict[str, Any]:
    detail = result.get("detail")
    if isinstance(detail, dict) and detail:
        return detail
    return result


def _looks_like_session(path: list[str], result: dict[str, Any]) -> bool:
    if "session" not in path:
        return False
    return "session_id" in result or "instance_id" in result or "status" in result


def _looks_like_job_context(result: dict[str, Any]) -> bool:
    return "job_id" in result and ("pattern" in result or "instance" in result)


def _operator_context_from_assist(result: dict[str, Any]) -> OperatorViewContext:
    return OperatorViewContext(
        session_id=_optional_str(result.get("session_id")),
        flow_id=_optional_str(result.get("flow_id")),
        scenario_id=_optional_str(result.get("scenario_id")),
        handoff_ready=bool(result.get("handoff_ready")),
    )


def _ensure_flow_session_flat(flat: dict[str, Any], path: list[str]) -> None:
    if len(path) >= 4 and path[0] == "flows" and path[2] == "session":
        session_id = path[3]
        flat.setdefault("session_id", session_id)
        if not flat.get("instance_id"):
            flat["instance_id"] = session_id
    if len(path) >= 2 and path[0] == "flows":
        flat.setdefault("flow_name", path[1])


def _operator_context_from_flow_path(path: list[str], flat: dict[str, Any]) -> OperatorViewContext:
    session_id = flat.get("instance_id") or flat.get("session_id")
    flow_id = flat.get("flow_name") or flat.get("flow")
    if len(path) >= 4 and path[0] == "flows" and path[2] == "session":
        session_id = session_id or path[3]
        flow_id = flow_id or path[1]
    return OperatorViewContext(
        session_id=_optional_str(session_id),
        flow_id=_optional_str(flow_id),
        path=list(path),
    )


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


def _design_proposal_id_from_path(path: list[str], result: dict[str, Any]) -> str | None:
    if len(path) >= 3 and path[0] == "design" and path[1] == "proposals":
        return path[2]
    proposal_id = result.get("proposal_id")
    return str(proposal_id) if proposal_id else None


def _append_format_query(url_path: str, params: dict[str, Any]) -> str:
    fmt = params.get("format")
    if not fmt:
        return url_path
    separator = "&" if "?" in url_path else "?"
    return f"{url_path}{separator}format={fmt}"


def _dispatch_definitions(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
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


def _dispatch_system(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
    params = params or {}
    if path == ["system", "doctor"]:
        return ctx.system.doctor(ctx.runtime)
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


def _dispatch_providers(ctx: Any, path: list[str], params: dict[str, Any]) -> Any:
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


def map_dispatch_to_rest(
    path: list[str],
    params: dict[str, Any] | None = None,
) -> tuple[str, str, dict[str, Any] | None, bool]:
    """Map a command path to REST method, url path, body, and auth flag."""
    params = params or {}
    body = dict(params.get("body") or params) or None
    prefix = path[0]

    if prefix == "assist":
        if path == ["assist", "scenarios"]:
            return "GET", "/v1/api/assist/scenarios", None, False
        if len(path) == 2 and path[1] == "scenarios":
            return "GET", f"/v1/api/assist/scenarios", None, False
        if len(path) == 2 and path[0] == "assist" and path[1] == "doctor":
            return "GET", "/v1/api/assist/doctor", None, False
        if len(path) == 3 and path[1] == "scenarios":
            return "GET", f"/v1/api/assist/scenarios/{path[2]}", None, False
        if len(path) == 4 and path[1] == "scenarios" and path[3] == "start":
            url = _append_format_query(f"/v1/api/assist/scenarios/{path[2]}/start", params)
            return "POST", url, body, True
        if len(path) == 2 and path[1] == "session":
            raise ValueError("session_id required")
        if len(path) == 3 and path[1] == "session":
            url = _append_format_query(f"/v1/api/assist/session/{path[2]}", params)
            return "GET", url, None, False
        if len(path) == 4 and path[1] == "session" and path[3] == "input":
            url = _append_format_query(f"/v1/api/assist/session/{path[2]}/input", params)
            return "POST", url, {"value": params.get("value", params.get("input"))}, True
        if len(path) == 4 and path[1] == "session" and path[3] == "backtrack":
            url = _append_format_query(f"/v1/api/assist/session/{path[2]}/backtrack", params)
            return "POST", url, {"to_step": params.get("to_step")}, True
        if len(path) == 4 and path[1] == "session" and path[3] == "resume":
            url = _append_format_query(f"/v1/api/assist/session/{path[2]}/resume", params)
            return "POST", url, None, True
        if len(path) == 4 and path[1] == "session" and path[3] == "cancel":
            return "POST", f"/v1/api/assist/session/{path[2]}/cancel", None, True
        if len(path) == 4 and path[1] == "session" and path[3] == "handoff":
            return "POST", f"/v1/api/assist/session/{path[2]}/handoff", None, False

    if prefix == "flows":
        if path == ["flows"]:
            return "GET", "/v1/api/flows", None, False
        if len(path) == 2:
            return "GET", f"/v1/api/flows/{path[1]}", None, False
        if len(path) == 3 and path[2] == "create":
            return "POST", f"/v1/api/flows/{path[1]}/create", body, True
        if len(path) == 4 and path[2] == "session":
            url = _append_format_query(f"/v1/api/flows/{path[1]}/session/{path[3]}", params)
            return "GET", url, None, False
        if len(path) == 5 and path[2] == "session" and path[4] == "input":
            url = _append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/input",
                params,
            )
            return "POST", url, {"value": params.get("value", params.get("input"))}, True
        if len(path) == 5 and path[2] == "session" and path[4] == "backtrack":
            url = _append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/backtrack",
                params,
            )
            return "POST", url, {"to_step": params.get("to_step")}, True
        if len(path) == 5 and path[2] == "session" and path[4] == "resume":
            url = _append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/resume",
                params,
            )
            return "POST", url, None, True
        if len(path) == 5 and path[2] == "session" and path[4] == "resume-child-wait":
            url = _append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/resume-child-wait",
                params,
            )
            return "POST", url, None, True
        if len(path) == 5 and path[2] == "session" and path[4] == "cancel":
            return "POST", f"/v1/api/flows/{path[1]}/session/{path[3]}/cancel", None, True

    if prefix == "processes":
        if len(path) == 3 and path[2] == "prepare":
            return "POST", f"/v1/api/processes/{path[1]}/prepare", body, True
        if path[-1] == "submit":
            return "POST", "/v1/api/processes/submit", body, True
        if len(path) == 3 and path[2] == "run":
            return "POST", f"/v1/api/processes/{path[1]}/run", body, True

    if prefix == "system" and path == ["system", "doctor"]:
        return "GET", "/v1/api/system/doctor", None, False

    raise ValueError(f"no REST mapping for dispatch path: {'/'.join(path)}")


__all__ = [
    "assist_routes_payload",
    "compact_dispatch_result",
    "dispatch_operator_path",
    "map_dispatch_to_rest",
    "normalize_assist_dispatch_args",
    "resolve_dispatch_format",
    "resolve_dispatch_path",
    "shape_dispatch_result",
]