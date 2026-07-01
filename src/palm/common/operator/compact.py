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
    include_operator_hint: bool = True,
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

    collection_field = prompt.get("collection_field")
    if collection_field:
        payload["collection_field"] = collection_field

    if wizard_view.get("committed"):
        payload["committed"] = True

    if "result" in fields and wizard_view.get("result") is not None:
        payload["result"] = wizard_view["result"]

    if include_operator_hint:
        hint = _operator_input_hint(payload)
        if hint:
            payload["operator_hint"] = hint

    return payload


def _operator_input_hint(payload: dict[str, Any]) -> str | None:
    if payload.get("waiting_for_child"):
        child = payload.get("child")
        if isinstance(child, dict) and child.get("instance_id"):
            return (
                f"drive child {child['instance_id']}; "
                "palm_flows_session_resume_child_wait only while waiting_for_child"
            )
        return (
            "inspect child session; palm_flows_session_resume_child_wait only while "
            "waiting_for_child"
        )

    phase = payload.get("collection_phase")
    if phase == "menu":
        return (
            "collection menu: palm_assist(params={session_id, flow_id, input|collection_action}) "
            "or palm_wizard_collection_action(action=add|done|edit|remove)"
        )
    if phase == "field":
        return "collection field: palm_flows_session_input(input=plain text)"
    if phase in ("select_item", "remove_confirm"):
        return "palm_flows_session_input(input=item number or label)"

    field_type = payload.get("field_type")
    if field_type == "confirm":
        return "palm_flows_session_input(input=yes|no)"
    if field_type == "choice":
        return "palm_flows_session_input(input=choice slug or number)"
    if payload.get("status") == "WAITING_FOR_INPUT":
        flow_id = payload.get("flow") or payload.get("flow_name")
        session_id = payload.get("instance_id") or payload.get("session_id")
        if flow_id and session_id:
            return (
                f"palm_assist(params={{session_id: {session_id!r}, flow_id: {flow_id!r}, value: …}}) "
                "or palm_flows_session_input(input=plain text)"
            )
        return "palm_flows_session_input(input=plain text)"
    if payload.get("status") in {"SUCCESS", "SUCCEEDED"} and payload.get("result") is not None:
        return "Job complete; see result or palm_system_fetch_instance(job_id)"
    return None


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


def compact_job_inspect(
    job_context: dict[str, Any],
    *,
    format: str = "compact",
    include: list[str] | None = None,
    truncate_answers_at: int = 2000,
) -> dict[str, Any]:
    """Reduce a full job context view to a compact operator snapshot."""
    if format == "verbose":
        return dict(job_context)

    fields = _DEFAULT_INCLUDE if include is None else frozenset(include)
    pattern = job_context.get("pattern")
    if not isinstance(pattern, dict):
        pattern = {}

    instance = job_context.get("instance") or {}
    if not isinstance(instance, dict):
        instance = {}

    payload: dict[str, Any] = {
        "job_id": job_context.get("job_id"),
        "instance_id": instance.get("instance_id"),
        "status": job_context.get("status"),
        "flow": instance.get("flow_name") or pattern.get("flow"),
        "step": pattern.get("step") or instance.get("current_step_slug"),
        "pattern": pattern.get("pattern"),
        "step_kind": pattern.get("step_kind"),
        "field_type": pattern.get("field_type"),
        "next_actions": _compact_next_actions(job_context.get("next_actions")),
    }

    if "prompt" in fields:
        payload["prompt"] = pattern.get("prompt")
        payload["prompt_title"] = pattern.get("prompt_title")

    if "validation" in fields:
        payload["validation_error"] = pattern.get("validation_error")

    waiting_for_child = bool(pattern.get("waiting_for_child"))
    payload["waiting_for_child"] = waiting_for_child

    if "children" in fields and waiting_for_child:
        child: dict[str, Any] = {}
        child_job_id = pattern.get("waiting_for_child_job_id")
        child_instance_id = pattern.get("waiting_for_child_instance_id")
        if child_job_id:
            child["job_id"] = child_job_id
        if child_instance_id:
            child["instance_id"] = child_instance_id
        child_status = pattern.get("child_status")
        if child_status:
            child["status"] = child_status
        if child:
            payload["child"] = child

    answers = pattern.get("answers")
    if isinstance(answers, dict) and "answers" in fields:
        payload["answers_keys"] = sorted(answers.keys())
        if truncate_answers_at > 0:
            payload["answers_preview"] = _truncate_answers(answers, truncate_answers_at)
        else:
            payload["answers"] = dict(answers)

    choices = pattern.get("choices")
    if choices:
        payload["choices"] = list(choices)

    if "result" in fields and job_context.get("result") is not None:
        payload["result"] = job_context["result"]

    return payload


__all__ = ["compact_job_inspect", "compact_wizard_inspect"]
