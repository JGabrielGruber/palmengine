"""Tests for wizard commit preview helper."""

from __future__ import annotations

from palm.common.operator.commit_preview import wizard_commit_preview


def test_commit_preview_uses_summary_and_hook() -> None:
    preview = wizard_commit_preview(
        {
            "instance_id": "inst-1",
            "job_id": "job-1",
            "flow_name": "onboard",
            "current_step_slug": "commit",
            "prompt": {
                "step_kind": "commit",
                "commit_hook": "save_profile",
                "summary": {"name": "Ada"},
            },
            "answers": {"name": "Ada", "email": "ada@example.com"},
        }
    )
    assert preview["commit_hook"] == "save_profile"
    assert preview["answers"] == {"name": "Ada"}
    assert preview["on_summary_or_commit"] is True


def test_commit_preview_falls_back_to_progress_hook() -> None:
    preview = wizard_commit_preview(
        {
            "instance_id": "inst-2",
            "wizard_progress": {"commit_hook": "persist"},
            "answers": {"x": 1},
        }
    )
    assert preview["commit_hook"] == "persist"
