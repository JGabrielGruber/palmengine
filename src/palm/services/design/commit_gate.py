"""Commit token gate for agent-driven design proposal publishes."""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import MutationRejectedError
from palm.common.operator.mutation_gate import (
    issue_input_token,
    mutation_secret,
    require_input_token_enabled,
    validate_input_token,
)

_COMMIT_STEP = "commit"


def issue_commit_token(proposal_id: str) -> dict[str, str]:
    """Issue a token bound to ``proposal_id`` for commit."""
    return issue_input_token(
        session_id=proposal_id,
        step_slug=_COMMIT_STEP,
        secret=mutation_secret(),
    )


def validate_commit_token(proposal_id: str, token: str | None) -> bool:
    """Validate commit token when strict mode is enabled."""
    if not require_input_token_enabled():
        return True
    if not token:
        return False
    return validate_input_token(
        token=token,
        session_id=proposal_id,
        step_slug=_COMMIT_STEP,
        secret=mutation_secret(),
    )


def build_commit_mutation_block(proposal_id: str, *, valid: bool) -> dict[str, Any] | None:
    """Attach commit authorization metadata after successful validate/impact."""
    if not valid:
        return {"mutations_allowed": False}
    gate = issue_commit_token(proposal_id)
    return {
        "mutations_allowed": True,
        "commit_token": gate["input_token"],
        "input_token": gate["input_token"],
        "expires_at": gate["expires_at"],
    }


def enforce_commit_token(
    proposal_id: str,
    *,
    commit_token: str | None = None,
    input_token: str | None = None,
) -> None:
    """Reject commit when strict mode requires a valid token."""
    token = commit_token or input_token
    if validate_commit_token(proposal_id, token):
        return
    raise MutationRejectedError(
        reason="missing_commit_token",
        session_id=proposal_id,
        step_slug=_COMMIT_STEP,
        detail=(
            "missing or invalid commit_token — run palm_design_validate or palm_design_impact "
            "and pass commit_token from the mutation block"
        ),
    )


__all__ = [
    "build_commit_mutation_block",
    "enforce_commit_token",
    "issue_commit_token",
    "validate_commit_token",
]