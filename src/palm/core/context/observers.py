"""
State change observer protocol — optional hooks for scope and value transitions.

Implementations live outside ``palm.core`` (e.g. event bus adapters in
``palm.common.state``). Core only defines the contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from palm.core.context.state_schema import StateSchema


class StateChangeObserver(Protocol):
    """Receive notifications when scoped state mutates."""

    def on_scope_enter(self, name: str, *, stack: tuple[str, ...]) -> None:
        """Called after a scope is pushed onto the stack."""

    def on_scope_exit(self, name: str, *, stack: tuple[str, ...]) -> None:
        """Called after a scope is popped from the stack."""

    def on_value_set(self, key: str, value: Any, *, scope: str | None) -> None:
        """Called after a root or scoped value is stored."""

    def on_schema_bound(
        self,
        schema: StateSchema | None,
        *,
        scope: str | None,
    ) -> None:
        """Called after a root or per-scope schema is attached."""
