"""Assistant views for design proposal workflow."""

from __future__ import annotations

from typing import Any

from palm.services.design.commit_gate import build_commit_mutation_block


def build_design_impact_assistant_view(
    proposal_id: str,
    impact: dict[str, Any],
    *,
    valid: bool = True,
) -> dict[str, Any]:
    """Human-first impact summary with commit/discard choices."""
    summary = impact.get("summary") if isinstance(impact.get("summary"), dict) else {}
    compatible = int(summary.get("compatible") or 0)
    blocked = int(summary.get("blocked") or 0)
    behind = int(summary.get("behind_latest") or 0)
    target = impact.get("target_revision")
    flow_id = impact.get("flow_id")

    hint_parts = [
        f"Flow {flow_id!r} would publish revision {target}.",
        f"{behind} instance(s) behind target; {compatible} compatible for auto-migrate.",
    ]
    if blocked:
        hint_parts.append(f"{blocked} blocked — will be skipped on commit.")

    mutation = build_commit_mutation_block(proposal_id, valid=valid)
    payload: dict[str, Any] = {
        "proposal_id": proposal_id,
        "flow_id": flow_id,
        "target_revision": target,
        "question": f"Commit design proposal {proposal_id} and auto-migrate compatible instances?",
        "choices": [
            {"slug": "commit", "label": "Publish revision and auto-migrate"},
            {"slug": "discard", "label": "Discard proposal"},
            {"slug": "revalidate", "label": "Re-run validation"},
        ],
        "hint": " ".join(hint_parts),
        "impact": impact,
        "actions": [
            {
                "tool": "palm_design_commit",
                "params": {"proposal_id": proposal_id},
                "when": "after validate + impact inspect",
            },
            {
                "tool": "palm_assist",
                "params": {
                    "path": ["design", "proposals", proposal_id, "commit"],
                    "params": {"proposal_id": proposal_id},
                },
            },
        ],
    }
    if mutation is not None:
        payload["mutation"] = mutation
    return payload


def build_design_validate_assistant_view(
    proposal_id: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Human-first validation result before impact inspect."""
    valid = bool(validation.get("valid"))
    mutation = build_commit_mutation_block(proposal_id, valid=valid)
    payload: dict[str, Any] = {
        "proposal_id": proposal_id,
        "valid": valid,
        "question": (
            "Proposal is valid — analyze impact next?"
            if valid
            else "Proposal failed validation — fix blockers or discard."
        ),
        "validation": validation,
        "choices": [
            {"slug": "impact", "label": "Analyze instance impact"},
            {"slug": "discard", "label": "Discard proposal"},
        ],
        "blockers": list(validation.get("blockers") or []),
    }
    if mutation is not None:
        payload["mutation"] = mutation
    return payload


__all__ = [
    "build_design_impact_assistant_view",
    "build_design_validate_assistant_view",
]