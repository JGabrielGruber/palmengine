"""
InputCapable — protocol for executables that accept delivered input.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from palm.core.context import BaseState


@runtime_checkable
class InputCapable(Protocol):
    """Executable that accepts a user value and writes it into job state."""

    def provide_input(self, state: BaseState, value: Any) -> str | None:
        """Deliver ``value`` to the active step; return a step slug when known."""


@runtime_checkable
class StepInspectable(Protocol):
    """Executable that exposes step position and collected answers."""

    def current_step_slug(self, state: BaseState) -> str | None: ...

    def answers(self, state: BaseState) -> dict[str, Any]: ...
