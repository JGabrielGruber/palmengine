"""
Wizard commit preview — payload a commit handler would receive.
"""

from __future__ import annotations

from typing import Any


def wizard_commit_preview(wizard_view: dict[str, Any]) -> dict[str, Any]:
    """Build the commit preview for a wizard instance read model."""
    prompt = wizard_view.get("prompt")
    if not isinstance(prompt, dict):
        prompt = {}

    answers = wizard_view.get("answers")
    if not isinstance(answers, dict):
        answers = {}

    progress = wizard_view.get("wizard_progress")
    if not isinstance(progress, dict):
        progress = {}

    step_kind = prompt.get("step_kind")
    commit_hook = prompt.get("commit_hook") or progress.get("commit_hook")
    summary = prompt.get("summary")
    preview_answers = dict(summary) if isinstance(summary, dict) else dict(answers)

    return {
        "instance_id": wizard_view.get("instance_id"),
        "job_id": wizard_view.get("job_id"),
        "flow": wizard_view.get("flow_name"),
        "step": wizard_view.get("current_step_slug") or prompt.get("step"),
        "step_kind": step_kind,
        "commit_hook": commit_hook,
        "answers": preview_answers,
        "answer_keys": sorted(preview_answers.keys()),
        "on_summary_or_commit": step_kind in {"summary", "commit"},
    }


__all__ = ["wizard_commit_preview"]