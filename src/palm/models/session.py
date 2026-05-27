"""
WizardSession - the persistent runtime state of a single wizard execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from palm.models.common import SessionStatus


class WizardSession(BaseModel):
    """
    Complete runtime state of a wizard execution.

    This is the primary object persisted to the database and passed around
    the engine. It is deliberately separate from the static WizardDefinition.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier (UUID4)")
    wizard_id: str = Field(description="References WizardDefinition.id")

    # Lifecycle
    status: SessionStatus = SessionStatus.CREATED
    current_step_slug: str | None = None

    # 0.2.0 Hierarchical support
    current_path: list[str] = Field(
        default_factory=list,
        description="Full path to the current step in the tree (e.g. ['personal_info', 'ask_name'])",
    )

    # Execution state
    collected_data: dict[str, Any] = Field(default_factory=dict)
    step_history: list[str] = Field(
        default_factory=list,
        description="Ordered list of step slugs visited (leaf steps). For full tree history see execution_path_history.",
    )
    back_stack: list[str] = Field(
        default_factory=list,
        description="Stack of step slugs (or qualified paths) the user can legally backtrack to",
    )

    # 0.2.0: More accurate tree-shaped execution history for proper hierarchical backtracking
    execution_path_history: list[list[str]] = Field(
        default_factory=list,
        description="History of full paths visited (supports true hierarchical navigation and backtracking)",
    )

    # Timing & TTL
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
        from palm.utils.time import utc_now

        self.last_activity_at = utc_now()

    def is_expired(self) -> bool:
        from palm.utils.time import is_expired

        return is_expired(self.expires_at)

    def record_step(self, slug: str, *, add_to_back_stack: bool = True) -> None:
        """Legacy flat recording. Prefer record_path for hierarchical wizards (0.2.0+)."""
        self.step_history.append(slug)
        self.current_step_slug = slug
        if add_to_back_stack and slug not in self.back_stack:
            self.back_stack.append(slug)

    def record_path(
        self,
        path: list[str],
        *,
        add_to_back_stack: bool = True,
        leaf_slug: str | None = None,
    ) -> None:
        """
        Record a full hierarchical path (preferred in 0.2.0+).

        path example: ["personal_info", "ask_name"]
        """
        if not path:
            return

        leaf = leaf_slug or path[-1]
        self.execution_path_history.append(list(path))
        self.current_path = list(path)
        self.current_step_slug = leaf
        self.step_history.append(leaf)

        if add_to_back_stack:
            # Store both the dotted path (for precision) and the leaf slug (for convenience)
            path_key = ".".join(path)
            if path_key not in self.back_stack:
                self.back_stack.append(path_key)
            leaf = path[-1]
            if leaf not in self.back_stack:
                self.back_stack.append(leaf)

    def pop_back_stack_to(self, target: str) -> list[str]:
        """
        Remove steps from back_stack after target (supports both slug and 'parent.child' paths).
        """
        if target not in self.back_stack:
            return []

        idx = self.back_stack.index(target)
        popped = self.back_stack[idx + 1 :]
        self.back_stack = self.back_stack[: idx + 1]
        return popped

    @property
    def current_step_path(self) -> list[str]:
        """Convenience accessor (0.2.1). Always prefers execution history."""
        if self.current_path:
            return self.current_path
        if self.execution_path_history:
            last = self.execution_path_history[-1]
            if last:
                return last
        if self.current_step_slug:
            return [self.current_step_slug]
        return []

    def ensure_path_consistency(self) -> None:
        """
        0.2.2: Make current_path the single source of truth.
        Reconstructs current_path from execution_path_history when needed.
        Also syncs current_step_slug.
        """
        if self.execution_path_history:
            last_path = self.execution_path_history[-1]
            if last_path:
                if not self.current_path or self.current_path != last_path:
                    self.current_path = list(last_path)
                if not self.current_step_slug or self.current_step_slug != last_path[-1]:
                    self.current_step_slug = last_path[-1]
        elif self.current_path:
            # No history but we have a path — seed the history
            self.execution_path_history = [list(self.current_path)]
            if not self.current_step_slug:
                self.current_step_slug = self.current_path[-1]
