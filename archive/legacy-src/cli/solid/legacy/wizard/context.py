"""
RichContext - the complete snapshot returned to clients before every user interaction.

This is the primary contract between the engine and any UI layer (CLI, TUI, WebSocket).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from palm.cli.solid.legacy.models.common import SessionStatus, StepType


class RichContext(BaseModel):
    """
    Complete situational awareness for the current pause point in a wizard (0.1.1).

    This is the **primary contract** between the Palm Core engine and any UI layer
    (CLI, Textual TUI, WebSocket clients, etc.).

    Key 0.1.1 additions:
    - `suggested_input`: Recommended value the user should type (especially for confirm steps)
    - `available_actions`: Explicit list of what the user can/should do right now

    The engine always emits a fresh RichContext before pausing for user input.
    """

    model_config = ConfigDict(extra="forbid")

    # Session & Wizard identity
    session_id: str
    wizard_id: str
    wizard_name: str

    # Current location
    current_step_slug: str
    current_step_type: StepType
    step_title: str

    # What to show the user
    prompt: str
    guidelines: str | None = None
    description: str | None = None

    # Input expectations
    input_type: str = Field(
        default="text",
        description="text | choice | confirm | summary | none",
    )
    choices: list[dict[str, Any]] | None = None
    validation_rules: list[dict[str, Any]] = Field(default_factory=list)
    required: bool = True

    # Navigation
    allowed_back_steps: list[str] = Field(
        default_factory=list,
        description="Slugs the user is currently allowed to backtrack to",
    )
    can_backtrack: bool = False

    # Execution path & data
    path: list[str] = Field(default_factory=list, description="Full step history so far")
    collected_data: dict[str, Any] = Field(default_factory=dict)

    # Session state
    status: SessionStatus
    is_first_step: bool = False

    # Hints for rich clients
    metadata: dict[str, Any] = Field(default_factory=dict)
    estimated_remaining_steps: int | None = None

    # Optional: pre-rendered nice display (CLI can use this)
    formatted_summary: str | None = None

    # New in 0.1.1: explicit guidance for the user
    suggested_input: str | None = Field(
        default=None,
        description="Example or recommended input for the current step (e.g. 'confirm', 'yes')",
    )
    available_actions: list[str] = Field(
        default_factory=list,
        description="Human-readable list of actions the user can take right now",
    )

    def to_display_dict(self) -> dict[str, Any]:
        """Compact representation suitable for CLI rendering."""
        return {
            "session": self.session_id[:8],
            "wizard": self.wizard_name,
            "step": f"{self.current_step_slug} ({self.current_step_type})",
            "prompt": self.prompt,
            "guidelines": self.guidelines,
            "choices": self.choices,
            "back": self.allowed_back_steps,
            "data_keys": list(self.collected_data.keys()),
        }
