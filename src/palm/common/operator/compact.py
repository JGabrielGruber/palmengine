"""
Compact wizard inspect — agent-friendly operator view without full state blobs.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_INCLUDE = frozenset(
    {
        "prompt",
        "answers",
        "children",
        "validation",
        "result",
    }
)


def compact_wizard_inspect(
    wizard_view: dict[str, Any],
    *,
    format: str = "compact",
    include: list[str] | None = None,
    truncate_answers_at: int = 2000,
) -> dict[str, Any]:
    """Reduce a full wizard read model to a compact operator snapshot."""
    if format == "verbose":
        return dict(wizard_view)

    fields = _DEFAULT_INCLUDE if include is None else frozenset(include)
    prompt = wizard_view.get("prompt") or {}
    answers = wizard_view.get("answers")
    if not isinstance(answers, dict):
        answers = {}

    payload: dict[str, Any] = {
        "instance_id": wizard_view.get("instance_id"),
        "job_id": wizard_view.get("job_id"),
        "flow": wizard_view.get("flow_name"),
        "status": wizard_view.get("status"),
        "step": wizard_view.get("current_step_slug") or prompt.get("step"),
        "step_kind": prompt.get("step_kind"),
        "field_type": prompt.get("field_type"),
        "next_actions": _compact_next_actions(wizard_view.get("next_actions")),
    }

    if "prompt" in fields:
        payload["prompt"] = prompt.get("text") or prompt.get("title")
        payload["prompt_title"] = prompt.get("title")

    if "validation" in fields:
        payload["validation_error"] = prompt.get("validation_error")

    waiting_for_child = bool(prompt.get("waiting_for_child"))
    payload["waiting_for_child"] = waiting_for_child

    if "children" in fields and waiting_for_child:
        child: dict[str, Any] = {}
        child_job_id = prompt.get("waiting_for_child_job_id")
        child_instance_id = prompt.get("waiting_for_child_instance_id")
        if child_job_id:
            child["job_id"] = child_job_id
        if child_instance_id:
            child["instance_id"] = child_instance_id
        child_status = prompt.get("child_status")
        if child_status:
            child["status"] = child_status
        if child:
            payload["child"] = child

    if "answers" in fields:
        payload["answers_keys"] = sorted(answers.keys())
        if truncate_answers_at > 0:
            payload["answers_preview"] = _truncate_answers(answers, truncate_answers_at)
        else:
            payload["answers"] = dict(answers)

    choices = prompt.get("choices")
    if choices:
        payload["choices"] = list(choices)

    collection_phase = prompt.get("collection_phase")
    if collection_phase:
        payload["collection_phase"] = collection_phase

    if wizard_view.get("committed"):
        payload["committed"] = True

    if "result" in fields and wizard_view.get("result") is not None:
        payload["result"] = wizard_view["result"]

    return payload


def _compact_next_actions(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    actions: list[str] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        action = entry.get("action")
        if isinstance(action, str) and action:
            actions.append(action)
    return actions


def _truncate_answers(answers: dict[str, Any], limit: int) -> dict[str, Any]:
    preview: dict[str, Any] = {}
    for key, value in answers.items():
        preview[key] = _truncate_value(value, limit)
    return preview


def _truncate_value(value: Any, limit: int) -> Any:
    if isinstance(value, str):
        if len(value) <= limit:
            return value
        return value[:limit] + "…"
    if isinstance(value, dict | list):
        rendered = str(value)
        if len(rendered) <= limit:
            return value
        return rendered[:limit] + "…"
    return value


__all__ = ["compact_wizard_inspect"]