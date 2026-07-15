"""
InputCapable — protocol for executables that accept delivered input.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from palm.core.context import BaseState

if TYPE_CHECKING:
    from palm.core.orchestration.job import Job


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


@runtime_checkable
class JobInspectable(Protocol):
    """Executable that can describe its own operator-facing job context.

    The generic inspector (:func:`palm.common.job_inspection.inspect_job`) only
    knows this capability — each pattern owns the extraction of its own scopes,
    branches, prompts, and schemas. No pattern-specific branching lives in the
    shared inspector.

    Returns a ``palm.common.job_inspection.JobContext``; annotated ``Any`` here
    because ``core`` must not import ``common`` (guard_core). Concrete pattern
    implementations narrow the return to ``JobContext``.
    """

    def inspect_job(self, job: Job) -> Any: ...
