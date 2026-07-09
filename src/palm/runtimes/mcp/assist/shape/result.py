"""Shape domain dispatch results for MCP / WS operator consumers."""

from __future__ import annotations

from typing import Any

from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    normalize_view_format,
)
from palm.runtimes.mcp.assist.shape.catalog import (
    shape_discover_assistant,
    shape_doctor_assistant,
    shape_flows_catalog_assistant,
    shape_waiting_assistant,
)
from palm.runtimes.mcp.assist.shape.design import (
    design_proposal_id_from_path,
    shape_design_publish_assistant,
)
from palm.runtimes.mcp.assist.shape.flow_create import shape_flow_create_assistant
from palm.runtimes.mcp.assist.shape.session import (
    assist_session_flat,
    ensure_flow_session_flat,
    input_schema_from_assist_turn,
    is_assistant_shaped,
    looks_like_job_context,
    looks_like_session,
    operator_context_from_assist,
    rebuild_assist_with_input_schema,
)
from palm.runtimes.mcp.flows.views import flatten_session_view, submission_view
from palm.services.assist.views import resolve_view_format
from palm.services.design.views import (
    build_design_impact_assistant_view,
    build_design_validate_assistant_view,
)


def coerce_dispatch_result(result: Any) -> Any:
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
    """Resolve view format for palm_assist (human-first)."""
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
    include_input_schema: bool = False,
) -> dict[str, Any]:
    """Shape domain dispatch results for MCP operator consumers.

    ``include_input_schema`` (default False) adds Portal ``input`` widgets.
    Keep off for MCP token budgets; WebSocket Assist sets True.
    """
    # Lazy-register assistant builder so isolated callers (tests, REST proxy) work.
    from palm.services.assist.views import ensure_assist_view_registration

    ensure_assist_view_registration()
    fmt = normalize_view_format(
        format or resolve_dispatch_format(path, params=params, tool_format=tool_format)
    )
    payload: dict[str, Any] = {"path": path}
    raw = result
    result = coerce_dispatch_result(result)
    prefix = path[0] if path else ""

    if isinstance(result, list):
        if prefix == "assist" and path[-2:] == ["catalog", "flows"]:
            payload.update(shape_flows_catalog_assistant(result))
            return payload
        if prefix == "assist" and path[-2:] == ["catalog", "waiting"]:
            payload.update(shape_waiting_assistant(result, params=params))
            return payload
        if prefix == "system" and path[-1:] == ["waiting"]:
            payload.update(shape_waiting_assistant(result, params=params))
            return payload
        payload["result"] = result
        return payload

    if not isinstance(result, dict):
        payload["result"] = result
        return payload

    if "handoff" in result:
        payload.update(result)
        return payload

    if prefix == "assist" and path[-1:] == ["discover"] and "hits" in result:
        if fmt == "assistant":
            payload.update(shape_discover_assistant(result))
        else:
            payload.update(result)
        return payload

    if prefix == "assist" and "session_id" in result:
        if fmt == "assistant" or result.get("question"):
            payload.update(result)
            if include_input_schema and fmt == "assistant" and "input" not in payload:
                schema = input_schema_from_assist_turn(payload)
                if schema is not None:
                    payload["input"] = schema
                else:
                    if not is_assistant_shaped(result):
                        rebuilt = rebuild_assist_with_input_schema(result)
                        if rebuilt is not None:
                            payload.update(rebuilt)
                            payload["path"] = path
            return payload
        if result.get("detail"):
            flat = assist_session_flat(result)
            shaped = build_operator_view(
                "powertool",
                flat_view=flat,
                context=operator_context_from_assist(result),
            )
            payload.update(shaped)
            for key in (
                "operator_hint",
                "compose_status",
                "handoff_ready",
                "scenario_id",
                "next_commands",
            ):
                if result.get(key) is not None:
                    payload[key] = result[key]
            return payload
        if "scenario_id" in result and "question" not in result:
            payload.update(submission_view(result))
            return payload

    if prefix == "flows" and looks_like_session(path, result):
        flat = flatten_session_view(raw)
        ensure_flow_session_flat(flat, path)
        payload.update(
            shape_flow_session_view(
                flat,
                format=fmt,
                session_id=flat.get("instance_id") or flat.get("session_id"),
                flow_id=flat.get("flow_name") or flat.get("flow"),
                path=path,
                invoke_tree=invoke_tree,
                include_input_schema=include_input_schema,
            )
        )
        return payload

    if prefix == "flows" and path[-1:] == ["create"]:
        if fmt == "assistant":
            payload.update(shape_flow_create_assistant(result, path=path))
        else:
            payload.update(submission_view(result))
        return payload

    if prefix == "system" and looks_like_job_context(result):
        payload.update(
            build_operator_view(
                fmt,
                flat_view=result,
                context=OperatorViewContext(path=list(path)),
            )
        )
        return payload

    if prefix == "system" and path[-1:] == ["doctor"]:
        if fmt == "assistant":
            payload.update(shape_doctor_assistant(result))
        else:
            payload["doctor"] = result
        return payload

    if prefix == "system" and path[-1:] == ["waiting"]:
        if fmt == "assistant":
            payload.update(shape_waiting_assistant(result, params=params))
        else:
            payload.update(result if isinstance(result, dict) else {"waiting": result})
        return payload

    if prefix == "assist" and path[-1:] == ["doctor"]:
        if fmt == "assistant":
            payload.update(shape_doctor_assistant(result))
        else:
            payload["doctor"] = result
        return payload

    if prefix == "assist" and len(path) >= 3 and path[1] == "catalog" and path[2] == "flows":
        if fmt == "assistant":
            payload.update(shape_flows_catalog_assistant(result))
        else:
            payload["flows"] = result
        return payload

    if prefix == "assist" and len(path) >= 3 and path[1] == "catalog" and path[2] == "waiting":
        if fmt == "assistant":
            payload.update(shape_waiting_assistant(result, params=params))
        else:
            payload["waiting"] = result
        return payload

    if prefix == "design" and fmt == "assistant":
        proposal_id = design_proposal_id_from_path(path, result)
        if proposal_id and path[-1:] == ["validate"] and isinstance(result, dict):
            payload.update(build_design_validate_assistant_view(proposal_id, result))
            return payload
        if proposal_id and path[-1:] == ["impact"] and isinstance(result, dict):
            valid = bool((result.get("mutation") or {}).get("mutations_allowed"))
            payload.update(
                build_design_impact_assistant_view(proposal_id, result, valid=valid)
            )
            return payload
        if path[-1:] in (["publish"], ["publish-resource"]) and isinstance(result, dict):
            payload.update(shape_design_publish_assistant(result))
            return payload

    payload.update(result)
    return payload


def compact_dispatch_result(
    path: list[str],
    result: Any,
    *,
    format: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shape with compact inspect defaults — powertool for non-assist/design paths."""
    if format is None:
        prefix = path[0] if path else ""
        tool_format = "assistant" if prefix in {"assist", "design"} else "powertool"
        resolved = resolve_dispatch_format(path, params=params, tool_format=tool_format)
    else:
        resolved = format
    return shape_dispatch_result(path, result, format=resolved, params=params)


__all__ = [
    "compact_dispatch_result",
    "resolve_dispatch_format",
    "shape_dispatch_result",
]
