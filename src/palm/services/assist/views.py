"""Assistant operator views — compose + humanize pipeline for assist surfaces."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compose_status import build_compose_status
from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.view_registry import (
    OperatorViewContext,
    register_operator_view_builder,
)
from palm.services.assist.registry import apply_assistant_enricher

def resolve_view_format(params: dict[str, Any] | None, *, default: str = "assistant") -> str:
    """Read ``format`` from dispatch/REST params with canonical normalization."""
    from palm.common.operator.view_registry import normalize_view_format

    if not params:
        return normalize_view_format(default)
    raw = params.get("format", default)
    return normalize_view_format(str(raw))


def ensure_assist_view_registration() -> None:
    """Register the assistant view builder with the operator view registry."""
    register_operator_view_builder("assistant", build_assistant_view)


def build_assistant_view(
    flat_view: dict[str, Any],
    *,
    context: OperatorViewContext,
) -> dict[str, Any]:
    """Build a human-first assistant turn from a flattened session inspect view."""
    flat = _flatten_view(flat_view)
    snapshot = compact_wizard_inspect(
        flat,
        include_operator_hint=False,
        stored_mutation_gate=context.stored_mutation_gate,
    )
    invoke_tree = context.invoke_tree or _invoke_tree_from_snapshot(snapshot)
    composed = build_compose_status(invoke_tree, snapshot)
    _merge_snapshot_fields(composed, snapshot)
    payload = _humanize_assistant_view(composed, context=context)
    scenario_id = context.scenario_id
    if scenario_id:
        payload = apply_assistant_enricher(scenario_id, payload, context=context)
    from palm.common.operator.collection_actions import build_collection_assistant_actions

    session_id = str(
        context.session_id
        or payload.get("session_id")
        or composed.get("instance_id")
        or ""
    )
    collection_actions = build_collection_assistant_actions(
        composed,
        session_id=session_id,
        flow_id=context.flow_id,
    )
    if collection_actions:
        payload["actions"] = collection_actions
    return payload


def _flatten_view(view: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(view, "to_dict"):
        payload = view.to_dict()
    elif isinstance(view, dict):
        payload = dict(view)
    else:
        return {"value": view}

    detail = payload.get("detail")
    if isinstance(detail, dict):
        merged = {**detail, **{k: v for k, v in payload.items() if k != "detail"}}
    else:
        merged = dict(payload)

    session_id = merged.get("session_id")
    if session_id is not None and merged.get("instance_id") is None:
        merged["instance_id"] = session_id
    return merged


def _merge_snapshot_fields(composed: dict[str, Any], snapshot: dict[str, Any]) -> None:
    for key in (
        "prompt",
        "prompt_title",
        "field_type",
        "step_kind",
        "collection_phase",
        "choices",
        "validation_error",
        "operator_mode",
    ):
        if snapshot.get(key) is not None and composed.get(key) is None:
            composed[key] = snapshot[key]


def _invoke_tree_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    session_id = snapshot.get("instance_id")
    tree: dict[str, Any] = {"instance_id": session_id}
    if snapshot.get("waiting_for_child"):
        child = snapshot.get("child")
        if isinstance(child, dict):
            tree["active_child"] = dict(child)
    return tree


def _humanize_assistant_view(
    composed: dict[str, Any],
    *,
    context: OperatorViewContext,
) -> dict[str, Any]:
    session_id = (
        context.session_id
        or composed.get("instance_id")
        or composed.get("session_id")
    )
    handoff_ready = bool(context.handoff_ready)

    operator_mode = composed.get("operator_mode")

    payload: dict[str, Any] = {
        "session_id": session_id,
        "status": _human_status(composed.get("status")),
        "question": _question_text(composed),
        "hint": _hint_text(composed),
        "handoff_ready": handoff_ready,
        "compose": _slim_compose(composed),
    }

    if context.scenario_id:
        payload["scenario_id"] = context.scenario_id
    if operator_mode:
        payload["operator_mode"] = operator_mode

    choices = _humanize_choices(composed.get("choices"))
    if choices:
        payload["choices"] = choices

    refs = _refs_block(composed, context)
    if refs:
        payload["refs"] = refs

    validation_error = composed.get("validation_error")
    if validation_error:
        payload["validation_error"] = validation_error

    if handoff_ready:
        payload["hint"] = _append_handoff_hint(str(payload.get("hint") or ""))

    from palm.common.operator.mutation_gate import build_mutation_envelope

    mutation = build_mutation_envelope(
        composed,
        stored_gate=context.stored_mutation_gate,
    )
    if mutation:
        payload["mutation"] = mutation

    return {key: value for key, value in payload.items() if value is not None}


def _human_status(raw: object | None) -> str:
    if raw is None:
        return "running"
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


def _question_text(composed: dict[str, Any]) -> str:
    if composed.get("waiting_for_child"):
        return "Waiting for nested flow to finish."

    phase = composed.get("collection_phase")
    if phase == "select_item":
        return str(composed.get("prompt_title") or composed.get("prompt") or "Which item?")

    prompt = composed.get("prompt")
    if isinstance(prompt, str) and prompt:
        return prompt
    title = composed.get("prompt_title")
    if isinstance(title, str) and title:
        return title
    return ""


def _hint_text(composed: dict[str, Any]) -> str:
    if composed.get("waiting_for_child"):
        return "Continue the child session, then resume here."

    phase = composed.get("collection_phase")
    if phase == "menu":
        return "Say add, edit, remove, or done."
    if phase == "field":
        return "Enter text for this item."
    if phase in {"select_item", "remove_confirm"}:
        return "Reply with item number or label."

    field_type = composed.get("field_type")
    if field_type == "confirm":
        return "Reply yes or no."
    if field_type == "choice" or composed.get("choices"):
        return "Reply with a number or choice name."
    if _human_status(composed.get("status")) == "waiting":
        return "Reply with your answer."
    return ""


def _humanize_choices(raw: Any) -> list[dict[str, Any]]:
    if not raw or not isinstance(raw, list):
        return []
    choices: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if isinstance(item, dict) and item.get("value") is not None:
            entry = dict(item)
            entry.setdefault("n", index)
            choices.append(entry)
            continue
        value = str(item)
        choices.append(
            {
                "n": index,
                "label": value.replace("-", " ").replace("_", " ").title(),
                "value": value,
            }
        )
    return choices


def _slim_compose(composed: dict[str, Any]) -> dict[str, Any]:
    slim: dict[str, Any] = {}
    step = composed.get("step")
    if step is not None:
        slim["step"] = step
    if "focus" in composed:
        slim["focus"] = composed.get("focus")

    active_child = composed.get("active_child")
    if isinstance(active_child, dict) and active_child:
        child = {
            key: active_child[key]
            for key in ("instance_id", "job_id", "status")
            if active_child.get(key) is not None
        }
        if child.get("status") is not None:
            child["status"] = _human_status(child["status"])
        slim["active_child"] = child

    ancestors = composed.get("ancestors")
    if isinstance(ancestors, list) and ancestors:
        slim["ancestor_count"] = len(ancestors)

    return slim


def _refs_block(composed: dict[str, Any], context: OperatorViewContext) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    job_id = composed.get("job_id")
    if job_id is not None:
        refs["job_id"] = job_id
    flow_id = context.flow_id or composed.get("flow")
    if flow_id is not None:
        refs["flow_id"] = flow_id
    return refs


def _append_handoff_hint(hint: str) -> str:
    suffix = "Ready to hand off — call assist session handoff or choose continue."
    if suffix.lower() in hint.lower():
        return hint
    if hint:
        return f"{hint} {suffix}"
    return suffix


_VERB_ACTION_LABELS: dict[str, str] = {
    "input": "Send answer",
    "backtrack": "Go back",
    "resume": "Resume session",
    "handoff": "Hand off to business flow",
    "cancel": "Cancel session",
}


def build_assistant_actions(session_ctx: Any) -> list[dict[str, Any]]:
    """Map ``next_commands`` to human-readable progressive-disclosure actions."""
    from palm.services.assist.registry import scenario_by_id

    session_id = str(session_ctx.session_id)
    scenario_id = session_ctx.scenario_id
    handoff_alias: str | None = None
    if scenario_id:
        contributor = scenario_by_id(scenario_id)
        if contributor:
            for alias, target in contributor.mcp_aliases:
                if target and target[-1] == "handoff":
                    handoff_alias = alias
                    break

    actions: list[dict[str, Any]] = []
    for path in session_ctx.next_commands:
        if not path or path[0] != "assist" or len(path) < 3 or path[1] != "session":
            continue
        verb = path[-1] if len(path) > 3 else None
        if verb == "handoff" and handoff_alias:
            actions.append(
                {
                    "label": _VERB_ACTION_LABELS["handoff"],
                    "alias": handoff_alias,
                    "params": {"session_id": session_id},
                }
            )
            continue
        if verb in _VERB_ACTION_LABELS:
            label = _VERB_ACTION_LABELS[verb]
        elif len(path) == 3 and path[1] == "session":
            label = "Inspect session"
        else:
            label = verb.replace("_", " ").title() if verb else "Continue"
        actions.append({"label": label, "path": list(path)})

    invoke_tree = session_ctx.invoke_tree
    if isinstance(invoke_tree, dict):
        active_child = invoke_tree.get("active_child")
        if isinstance(active_child, dict):
            child_id = active_child.get("instance_id")
            if child_id:
                actions.append(
                    {
                        "label": "Open child session",
                        "path": ["flows", "session", str(child_id)],
                    }
                )

    return actions


__all__ = [
    "build_assistant_actions",
    "build_assistant_view",
    "ensure_assist_view_registration",
    "resolve_view_format",
]