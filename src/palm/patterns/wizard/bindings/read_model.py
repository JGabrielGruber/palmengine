"""
Wizard REST read model — instance-keyed view for interactive flows.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import JobStatus


def build_wizard_view(
    instance: dict[str, Any],
    *,
    wizard_progress: dict[str, Any] | None = None,
    pattern: dict[str, Any] | None = None,
    job_status: str | None = None,
) -> dict[str, Any]:
    """Assemble a wizard-centric view keyed by durable ``instance_id``."""
    instance_id = str(instance["instance_id"])
    job_id = str(instance.get("job_id") or instance_id)
    status = job_status or instance.get("status")

    payload: dict[str, Any] = {
        "instance_id": instance_id,
        "job_id": job_id,
        "status": status,
        "flow_name": instance.get("flow_name"),
        "process_name": instance.get("process_name"),
        "current_step_slug": instance.get("current_step_slug")
        or instance.get("wizard_step_slug"),
        "wizard_progress": wizard_progress,
        "prompt": _prompt_block(pattern),
        "answers": _answers_block(pattern, wizard_progress),
        "committed": _is_committed(pattern, wizard_progress),
        "links": {
            "self": f"/v1/wizards/{instance_id}",
            "instance": f"/v1/instances/{instance_id}",
            "job": f"/v1/jobs/{job_id}",
        },
        "next_actions": derive_wizard_next_actions(
            instance_id=instance_id,
            job_id=job_id,
            status=status,
        ),
    }
    if pattern is not None:
        payload["pattern"] = pattern.get("pattern", "wizard")
    return payload


def derive_wizard_next_actions(
    *,
    instance_id: str,
    job_id: str,
    status: str | None,
) -> list[dict[str, Any]]:
    """Suggest REST actions available for a wizard instance."""
    actions: list[dict[str, Any]] = []

    if status == JobStatus.WAITING_FOR_INPUT.value:
        actions.append(
            {
                "action": "resume_child_wait",
                "method": "POST",
                "path": f"/v1/wizards/{instance_id}/resume-child-wait",
                "description": "Re-check nested child wizard and advance when complete",
            }
        )
        actions.append(
            {
                "action": "provide_wizard_input",
                "method": "POST",
                "path": f"/v1/wizards/{instance_id}/input",
                "description": "Deliver interactive wizard input",
            }
        )
        actions.append(
            {
                "action": "request_backtrack",
                "method": "POST",
                "path": f"/v1/wizards/{instance_id}/backtrack",
                "description": "Backtrack to a prior wizard step",
            }
        )

    actions.append(
        {
            "action": "get_wizard",
            "method": "GET",
            "path": f"/v1/wizards/{instance_id}",
            "description": "Refresh wizard status and current prompt",
        }
    )
    actions.append(
        {
            "action": "get_instance",
            "method": "GET",
            "path": f"/v1/instances/{instance_id}",
            "description": "Inspect durable process instance",
        }
    )
    actions.append(
        {
            "action": "get_job",
            "method": "GET",
            "path": f"/v1/jobs/{job_id}",
            "description": "Slim job status",
        }
    )
    return actions


def _prompt_block(pattern: dict[str, Any] | None) -> dict[str, Any] | None:
    if pattern is None:
        return None
    prompt: dict[str, Any] = {
        "step": pattern.get("step"),
        "title": pattern.get("prompt_title"),
        "text": pattern.get("prompt"),
        "field_type": pattern.get("field_type"),
        "effective_schema_type": pattern.get("effective_schema_type"),
        "validation_error": pattern.get("validation_error"),
        "scope_path": pattern.get("scope_path"),
    }
    choices = pattern.get("choices")
    if choices:
        prompt["choices"] = list(choices)
    collection_phase = pattern.get("collection_phase")
    if collection_phase:
        prompt["collection_phase"] = collection_phase
    collection_items = pattern.get("collection_items")
    if collection_items:
        prompt["collection_items"] = list(collection_items)
    collection_item_previews = pattern.get("collection_item_previews")
    if collection_item_previews:
        prompt["collection_item_previews"] = list(collection_item_previews)
    collection_draft = pattern.get("collection_draft")
    if isinstance(collection_draft, dict) and collection_draft:
        prompt["collection_draft"] = dict(collection_draft)
    for key in (
        "waiting_for_child",
        "waiting_for_child_job_id",
        "waiting_for_child_instance_id",
        "child_status",
        "child_job_href",
        "child_instance_href",
        "collection_progress",
        "collection_field",
        "collection_select_action",
        "collection_remove_index",
        "step_kind",
        "label_field",
        "min_items",
    ):
        value = pattern.get(key)
        if value is not None:
            prompt[key] = value
    item_fields = pattern.get("item_fields")
    if item_fields:
        prompt["item_fields"] = list(item_fields)
    transform_rule = pattern.get("transform_rule")
    if transform_rule:
        prompt["transform_rule"] = transform_rule
    if prompt.get("step") is None and prompt.get("text") is None:
        return None
    return prompt


def _answers_block(
    pattern: dict[str, Any] | None,
    wizard_progress: dict[str, Any] | None,
) -> dict[str, Any]:
    if pattern is not None:
        answers = pattern.get("answers")
        if isinstance(answers, dict) and answers:
            return dict(answers)
    return {}


def _is_committed(
    pattern: dict[str, Any] | None,
    wizard_progress: dict[str, Any] | None,
) -> bool:
    if wizard_progress is not None:
        commit_status = wizard_progress.get("commit_status")
        if commit_status == "succeeded":
            return True
    return False


__all__ = ["build_wizard_view", "derive_wizard_next_actions"]