"""
Approval workflow — multi-step validation, summary, and commit.

Models a lightweight spend approval: requester details, amount, approver,
then transactional commit via a named handler.
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard.handler import CommitResult, default_commit_registry

APPROVAL_FLOW = FlowDefinition(
    id="flow-approval",
    name="approval",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "record_approval",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "title",
                "title": "Request Title",
                "prompt": "Short title for this approval request",
                "validation": [{"rule": "min_length", "params": {"min": 5}}],
            },
            {
                "slug": "amount",
                "title": "Amount (USD)",
                "prompt": "Enter the amount in dollars (numbers only)",
                "validation": [
                    {
                        "rule": "regex",
                        "params": {
                            "pattern": r"^\d+(\.\d{1,2})?$",
                            "message": "Enter a valid amount (e.g. 1500 or 99.50)",
                        },
                    }
                ],
            },
            {
                "slug": "approver",
                "title": "Approver",
                "prompt": "Who should approve this request?",
                "field_type": "choice",
                "choices": ["team-lead", "director", "finance"],
            },
            {
                "slug": "justification",
                "title": "Justification",
                "prompt": "Why is this spend needed?",
                "validation": [{"rule": "min_length", "params": {"min": 10}}],
            },
        ],
    },
)

APPROVAL_PROCESS = ProcessDefinition(
    id="proc-approval",
    name="approval-workflow",
    flows=[APPROVAL_FLOW],
    metadata={
        "example": True,
        "description": "Spend approval with validation and commit handler",
    },
)


def _record_approval(ctx: Any) -> CommitResult:
    amount_raw = ctx.answers.get("amount")
    try:
        amount = float(str(amount_raw))
    except (TypeError, ValueError):
        return CommitResult.failure("Invalid amount")

    if amount <= 0:
        return CommitResult.failure("Amount must be positive")

    ticket = {
        "title": ctx.answers.get("title"),
        "amount_usd": amount,
        "approver": ctx.answers.get("approver"),
        "justification": ctx.answers.get("justification"),
        "status": "pending",
    }
    return CommitResult.success({"approval": ticket})


def register_definitions(repository: object) -> None:
    default_commit_registry().register("record_approval", _record_approval)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(APPROVAL_FLOW)
    if callable(save_process):
        save_process(APPROVAL_PROCESS)
