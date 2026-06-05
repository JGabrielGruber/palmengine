"""
WizardSession - the persistent runtime state of a single wizard execution.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .common import SessionStatus


class WizardSession(BaseModel):
    """
    Complete runtime state of a wizard execution.

    This is the primary object persisted to the database and passed around
    the engine. It is deliberately separate from the static WizardDefinition.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # Identity
    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique session identifier (UUID4)"
    )
    wizard_id: str = Field(description="References WizardDefinition.id")

    # Lifecycle
    status: SessionStatus = SessionStatus.CREATED
    current_step_slug: str | None = None

    # Execution state
    collected_data: dict[str, Any] = Field(default_factory=dict)
    step_history: list[str] = Field(
        default_factory=list,
        description="Ordered list of step slugs visited (including current)",
    )
    back_stack: list[str] = Field(
        default_factory=list,
        description="Stack of step slugs the user can legally backtrack to",
    )

    # Timing & TTL
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None

    # Outcome
    commit_result: dict[str, Any] | None = None
    error: str | None = None
    error_step: str | None = None

    # Rich context cache (last emitted) - useful for replay
    last_rich_context: dict[str, Any] | None = Field(
        default=None,
        description="Serialized RichContext for quick resume / admin inspection",
    )

    def touch(self) -> None:
        """Update last_activity_at to now (UTC)."""
        from palm.cli.solid.legacy.utils.time import utc_now

        self.last_activity_at = utc_now()

    def is_expired(self) -> bool:
        from palm.cli.solid.legacy.utils.time import is_expired

        return is_expired(self.expires_at)

    def record_step(self, slug: str, *, add_to_back_stack: bool = True) -> None:
        """Append step to history and optionally to back stack."""
        self.step_history.append(slug)
        self.current_step_slug = slug
        if add_to_back_stack and slug not in self.back_stack:
            self.back_stack.append(slug)

    def pop_back_stack_to(self, target_slug: str) -> list[str]:
        """
        Remove steps from back_stack after target_slug.
        Returns the popped steps (for auditing).
        """
        if target_slug not in self.back_stack:
            return []

        idx = self.back_stack.index(target_slug)
        popped = self.back_stack[idx + 1 :]
        self.back_stack = self.back_stack[: idx + 1]
        return popped
