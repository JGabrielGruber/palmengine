"""Session / assist-turn helpers for shape_dispatch_result."""

from __future__ import annotations

from typing import Any

from palm.common.operator.view_registry import OperatorViewContext


def optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


def is_assistant_shaped(result: dict[str, Any]) -> bool:
    """True when result is already a humanized assist turn (not raw inspect)."""
    if result.get("question") is not None and result.get("mutation") is not None:
        return True
    if isinstance(result.get("compose"), dict) and result.get("status") in {
        "waiting",
        "complete",
        "failed",
        "running",
    }:
        return True
    return False


def input_schema_from_assist_turn(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Build Portal ``input`` from an already-humanized assist turn (0.32.6)."""
    try:
        from palm.services.assist.present.input_schema import build_input_schema
    except Exception:
        return None
    compose = payload.get("compose") if isinstance(payload.get("compose"), dict) else {}
    mutation = payload.get("mutation") if isinstance(payload.get("mutation"), dict) else {}
    choices = payload.get("choices") if isinstance(payload.get("choices"), list) else None
    status = payload.get("status")
    step = compose.get("step") or mutation.get("step_slug")
    field_type: str | None = None
    step_kind = "input"
    if mutation.get("confirm_step") or step in {"summary", "commit"}:
        step_kind = "summary" if step != "commit" else "commit"
        field_type = "confirm"
    elif choices:
        field_type = "choice"
        step_kind = "input"
    elif status == "waiting":
        field_type = "text"
    composed: dict[str, Any] = {
        "status": status,
        "step": step,
        "slug": step,
        "step_kind": step_kind,
        "field_type": field_type,
        "prompt": payload.get("question"),
        "required": True,
        "validation_error": payload.get("validation_error"),
    }
    if choices:
        composed["choices"] = choices
    return build_input_schema(composed, choices=choices)


def rebuild_assist_with_input_schema(result: dict[str, Any]) -> dict[str, Any] | None:
    """Re-humanize a *flat inspect* dict with Portal ``input`` widgets."""
    try:
        from palm.services.assist.views import build_assistant_view
    except Exception:
        return None
    flat = assist_session_flat(result)
    if not isinstance(flat, dict):
        return None
    sid = result.get("session_id") or flat.get("session_id") or flat.get("instance_id")
    if sid is not None:
        flat.setdefault("session_id", sid)
        flat.setdefault("instance_id", sid)
    ctx = OperatorViewContext(
        session_id=optional_str(sid),
        flow_id=optional_str(
            result.get("flow_id") or flat.get("flow_name") or flat.get("flow")
        ),
        scenario_id=optional_str(result.get("scenario_id")),
        handoff_ready=bool(result.get("handoff_ready")),
        include_input_schema=True,
        intent=optional_str(
            (result.get("answers_summary") or "").split("intent=", 1)[-1]
            if "intent=" in str(result.get("answers_summary") or "")
            else None
        ),
    )
    answers = flat.get("answers") if isinstance(flat.get("answers"), dict) else None
    if isinstance(answers, dict) and answers.get("intent") is not None:
        ctx.intent = str(answers["intent"])
        ctx.answers_preview = {"intent": ctx.intent}
    shaped = build_assistant_view(flat, context=ctx)
    if result.get("actions") and not shaped.get("actions"):
        shaped["actions"] = result["actions"]
    for key in ("handoff_ready", "scenario_id", "session_id", "answers_summary"):
        if result.get(key) is not None and shaped.get(key) is None:
            shaped[key] = result[key]
    return shaped


def assist_session_flat(result: dict[str, Any]) -> dict[str, Any]:
    detail = result.get("detail")
    if isinstance(detail, dict) and detail:
        return detail
    return result


def looks_like_session(path: list[str], result: dict[str, Any]) -> bool:
    if "session" not in path:
        return False
    return "session_id" in result or "instance_id" in result or "status" in result


def looks_like_job_context(result: dict[str, Any]) -> bool:
    return "job_id" in result and ("pattern" in result or "instance" in result)


def operator_context_from_assist(result: dict[str, Any]) -> OperatorViewContext:
    return OperatorViewContext(
        session_id=optional_str(result.get("session_id")),
        flow_id=optional_str(result.get("flow_id")),
        scenario_id=optional_str(result.get("scenario_id")),
        handoff_ready=bool(result.get("handoff_ready")),
    )


def ensure_flow_session_flat(flat: dict[str, Any], path: list[str]) -> None:
    if len(path) >= 4 and path[0] == "flows" and path[2] == "session":
        session_id = path[3]
        flat.setdefault("session_id", session_id)
        if not flat.get("instance_id"):
            flat["instance_id"] = session_id
    if len(path) >= 2 and path[0] == "flows":
        flat.setdefault("flow_name", path[1])


def operator_context_from_flow_path(
    path: list[str], flat: dict[str, Any]
) -> OperatorViewContext:
    session_id = flat.get("instance_id") or flat.get("session_id")
    flow_id = flat.get("flow_name") or flat.get("flow")
    if len(path) >= 4 and path[0] == "flows" and path[2] == "session":
        session_id = session_id or path[3]
        flow_id = flow_id or path[1]
    return OperatorViewContext(
        session_id=optional_str(session_id),
        flow_id=optional_str(flow_id),
        path=list(path),
    )


__all__ = [
    "assist_session_flat",
    "ensure_flow_session_flat",
    "input_schema_from_assist_turn",
    "is_assistant_shaped",
    "looks_like_job_context",
    "looks_like_session",
    "operator_context_from_assist",
    "operator_context_from_flow_path",
    "optional_str",
    "rebuild_assist_with_input_schema",
]
