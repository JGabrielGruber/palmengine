"""Handoff resolution for assist sessions (flow or design)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.services.assist._view_meta import answers_from_view, assist_metadata

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService

_DESIGN_ACTION_BY_INTENT: dict[str, str] = {
    "create-flow": "publish_flow",
    "improve-flow": "publish_flow",
    "propose-resource": "publish_resource",
}


def create_params_from_answers(
    assist_meta: dict[str, Any],
    answers: dict[str, Any],
) -> dict[str, Any]:
    """Map answer keys → create_params via assist metadata (0.30.3)."""
    mapping = assist_meta.get("create_params_from_answers")
    if not isinstance(mapping, dict) or not mapping:
        return {}
    params: dict[str, Any] = {}
    for param_key, answer_key in mapping.items():
        if not isinstance(param_key, str) or not isinstance(answer_key, str):
            continue
        if answer_key in answers and answers[answer_key] is not None:
            params[param_key] = answers[answer_key]
    return params


def design_handoff_payload(
    intent: object,
    answers: dict[str, Any],
    assist_meta: dict[str, Any],
) -> dict[str, Any]:
    """Build ``kind: design`` handoff envelope (0.30.3)."""
    intent_s = str(intent)
    none_hints = assist_meta.get("handoff_none_hints") or {}
    default_hint = (
        "Use palm_design_publish_flow (or palm_design_publish_resource). "
        "Treat unknown handoff kinds like none and always read operator_hint."
    )
    operator_hint = default_hint
    if isinstance(none_hints, dict):
        mapped = none_hints.get(intent_s)
        if isinstance(mapped, str) and mapped.strip():
            operator_hint = mapped

    name_raw = answers.get("name_or_base")
    name = str(name_raw).strip() if name_raw is not None and str(name_raw).strip() else None

    payload: dict[str, Any] = {
        "kind": "design",
        "flow_id": None,
        "session_id": None,
        "create_params": {},
        "intent": intent_s,
        "design_action": _DESIGN_ACTION_BY_INTENT.get(intent_s, "propose_flow"),
        "operator_hint": operator_hint,
    }
    if intent_s == "improve-flow" and name:
        payload["base_flow_id"] = name
    if intent_s in {"create-flow", "propose-resource"} and name:
        payload["suggested_name"] = name
    return payload


def resolve_handoff(service: AssistService, session_id: str) -> dict[str, Any]:
    """Resolve handoff envelope for an assist session."""
    handle = service.session(session_id)
    ctx = handle.context()
    assist_meta = assist_metadata(service, handle.flow_id)
    answers = answers_from_view(ctx.detail)
    intent = answers.get("intent")
    handoff_map = assist_meta.get("handoff_map") or {}
    target = handoff_map.get(intent) if intent is not None else None
    if target is None and intent in (assist_meta.get("handoff_flows") or []):
        target = intent
    if target:
        create_params = create_params_from_answers(assist_meta, answers)
        return {
            "handoff": {
                "kind": "flow",
                "flow_id": target,
                "session_id": None,
                "create_params": create_params,
                "operator_hint": (
                    f"Use palm_flows_create_session or POST /v1/api/flows/{target}/create"
                ),
            }
        }
    design_intents = assist_meta.get("design_handoff_intents") or ()
    if intent is not None and intent in design_intents:
        return {"handoff": design_handoff_payload(intent, answers, assist_meta)}

    default_none_hint = "Assist session complete — no business flow handoff requested."
    none_hints = assist_meta.get("handoff_none_hints") or {}
    operator_hint = default_none_hint
    if intent is not None and isinstance(none_hints, dict):
        mapped = none_hints.get(intent)
        if isinstance(mapped, str) and mapped.strip():
            operator_hint = mapped
    return {
        "handoff": {
            "kind": "none",
            "flow_id": None,
            "session_id": None,
            "create_params": {},
            "operator_hint": operator_hint,
        }
    }


__all__ = [
    "create_params_from_answers",
    "design_handoff_payload",
    "resolve_handoff",
]
