"""Human-readable turn fields: question, hint, choices, compose, terminal blurb."""

from __future__ import annotations

from typing import Any

from palm.common.operator.mutation_gate import build_mutation_envelope
from palm.common.operator.view_registry import OperatorViewContext
from palm.services.assist.present.actions import resource_assistant_actions
from palm.services.assist.present.input_schema import (
    build_input_schema,
    resolve_field_required,
)
from palm.services.assist.present.status import human_status


def question_text(composed: dict[str, Any]) -> str:
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


def hint_text(composed: dict[str, Any]) -> str:
    if composed.get("waiting_for_child"):
        return "Continue the child session, then resume here."

    phase = composed.get("collection_phase")
    if phase == "menu":
        return "Say add, edit, remove, or done."
    if phase == "field":
        if resolve_field_required(composed) is False:
            return "Optional — enter a value, or Skip / leave empty."
        if composed.get("field_type") == "choice" or composed.get("choices"):
            return "Pick a choice or type a value."
        return "Enter text for this item."
    if phase in {"select_item", "remove_confirm"}:
        return "Reply with item number or label."

    field_type = composed.get("field_type")
    if field_type == "confirm":
        return "Reply yes or no."
    if field_type == "choice" or composed.get("choices"):
        return "Reply with a number or choice name."
    if human_status(composed.get("status")) == "waiting":
        return "Reply with your answer."
    return ""


def humanize_choices(raw: Any) -> list[dict[str, Any]]:
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


def slim_compose(composed: dict[str, Any]) -> dict[str, Any]:
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
            child["status"] = human_status(child["status"])
        slim["active_child"] = child

    ancestors = composed.get("ancestors")
    if isinstance(ancestors, list) and ancestors:
        slim["ancestor_count"] = len(ancestors)

    return slim


def refs_block(composed: dict[str, Any], context: OperatorViewContext) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    job_id = composed.get("job_id")
    if job_id is not None:
        refs["job_id"] = job_id
    flow_id = context.flow_id or composed.get("flow")
    if flow_id is not None:
        refs["flow_id"] = flow_id
    return refs


def append_handoff_hint(hint: str) -> str:
    suffix = "Ready to hand off — call assist session handoff or choose continue."
    if suffix.lower() in hint.lower():
        return hint
    if hint:
        return f"{hint} {suffix}"
    return suffix


def slim_answer_summary(preview: object, *, max_keys: int = 6, max_len: int = 160) -> str:
    """Compact key=value line for terminal turns (token-thrifty)."""
    if not isinstance(preview, dict) or not preview:
        return ""
    parts: list[str] = []
    for key in sorted(preview.keys()):
        if len(parts) >= max_keys:
            parts.append("…")
            break
        value = preview[key]
        if isinstance(value, list):
            labels: list[str] = []
            for item in value[:3]:
                if isinstance(item, dict):
                    label = item.get("title") or item.get("name") or item.get("label")
                    if label is not None:
                        labels.append(str(label)[:24])
                elif item is not None:
                    labels.append(str(item)[:24])
            if labels:
                text = f"{len(value)} item(s): {', '.join(labels)}"
                if len(value) > 3:
                    text += "…"
            else:
                text = f"{len(value)} item(s)"
            parts.append(f"{key}={text}")
            continue
        if isinstance(value, dict):
            continue
        text = str(value).strip()
        if not text:
            continue
        if len(text) > 40:
            text = text[:40] + "…"
        parts.append(f"{key}={text}")
    if not parts:
        return ""
    joined = ", ".join(parts)
    if len(joined) > max_len:
        return joined[: max_len - 1] + "…"
    return joined


def apply_terminal_blurb(payload: dict[str, Any], composed: dict[str, Any]) -> None:
    """Fill empty terminal turns with a short completion line + slim answer summary."""
    status = str(payload.get("status") or "")
    summary = slim_answer_summary(composed.get("answers_preview"))
    if status == "complete":
        if summary:
            thin = str(payload.get("question") or "")
            if (
                not thin
                or thin.startswith("Finished. Answers: intro=")
                or thin == "Flow finished successfully."
            ):
                payload["question"] = f"Finished. Answers: {summary}"
            payload["answers_summary"] = summary
        elif not payload.get("question"):
            payload["question"] = "Flow finished successfully."
        if not payload.get("handoff_ready"):
            payload["hint"] = (
                "Session complete — start another flow or return to operator entry."
            )
        elif not payload.get("hint"):
            payload["hint"] = "Session complete — no further input."
    elif status == "failed":
        if not payload.get("question"):
            payload["question"] = "Flow failed."
        if not payload.get("hint"):
            err = composed.get("validation_error") or composed.get("resource_error")
            payload["hint"] = str(err) if err else "Inspect the session or start a new run."


def humanize_assistant_view(
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
        "status": human_status(composed.get("status")),
        "question": question_text(composed),
        "hint": hint_text(composed),
        "handoff_ready": handoff_ready,
        "compose": slim_compose(composed),
    }

    if context.scenario_id:
        payload["scenario_id"] = context.scenario_id
    if operator_mode:
        payload["operator_mode"] = operator_mode

    choices = humanize_choices(composed.get("choices"))
    if choices:
        payload["choices"] = choices

    if getattr(context, "include_input_schema", False):
        input_schema = build_input_schema(composed, choices=choices)
        if input_schema:
            payload["input"] = input_schema

    refs = refs_block(composed, context)
    if refs:
        payload["refs"] = refs

    validation_error = composed.get("validation_error")
    if validation_error:
        payload["validation_error"] = validation_error

    resource_error = composed.get("resource_error")
    if resource_error is not None:
        payload["resource_error"] = resource_error
    resource_remediation = composed.get("resource_remediation")
    if resource_remediation:
        payload["resource_remediation"] = resource_remediation
        payload["hint"] = str(resource_remediation)

    if handoff_ready:
        payload["hint"] = append_handoff_hint(str(payload.get("hint") or ""))

    mutation = build_mutation_envelope(
        composed,
        stored_gate=context.stored_mutation_gate,
    )
    if mutation:
        payload["mutation"] = mutation

    status = str(payload.get("status") or "")
    if status in {"complete", "failed"}:
        apply_terminal_blurb(payload, composed)

    resource_actions = resource_assistant_actions(
        composed,
        session_id=str(session_id) if session_id else None,
        flow_id=context.flow_id,
    )
    if resource_actions:
        payload["actions"] = resource_actions

    return {key: value for key, value in payload.items() if value is not None}


__all__ = [
    "append_handoff_hint",
    "apply_terminal_blurb",
    "hint_text",
    "humanize_assistant_view",
    "humanize_choices",
    "question_text",
    "refs_block",
    "slim_answer_summary",
    "slim_compose",
]
