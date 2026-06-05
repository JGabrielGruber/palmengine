"""
Common enums and shared model primitives used across Palm.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StepType(StrEnum):
    """Types of steps a wizard can contain."""

    INTRODUCTION = "introduction"  # Always first, explicit confirmation, never backtrackable
    DISPLAY = "display"  # Informational, user presses enter/confirm to continue
    USER_INPUT = "user_input"  # Free text or structured input with validation
    CHOICE = "choice"  # Multiple choice / select one
    CONFIRM = "confirm"  # Yes/no confirmation (often before commit)
    SUMMARY = "summary"  # Review collected data before final commit
    COMMIT = "commit"  # Terminal transactional step (idempotent & durable)
    ACTION = "action"  # Non-interactive side-effect (logging, API call, etc.)


class SessionStatus(StrEnum):
    """Lifecycle states for a wizard session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED_FOR_INPUT = "paused_for_input"
    AWAITING_COMMIT = "awaiting_commit"
    COMMITTED = "committed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ValidationRule(BaseModel):
    """
    Declarative validation rule attached to a step.

    The engine (or custom validators) interpret these.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        description="Rule type: required, min_length, max_length, min_value, max_value, regex, email, custom"
    )
    params: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = Field(
        default=None,
        description="Custom error message. If omitted, a default is generated.",
    )

    def to_error(self, field: str | None = None) -> str:
        """Produce a human-readable error string."""
        if self.error_message:
            return self.error_message
        base = f"Validation failed on rule '{self.type}'"
        if field:
            base = f"{field}: {base}"
        return base
