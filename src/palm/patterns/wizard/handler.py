"""
Wizard commit handlers — transactional finalize hooks for wizard flows.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState

if TYPE_CHECKING:
    from palm.core.resource import ResourceEngine

CommitHandler = Callable[["CommitContext"], "CommitResult"]


@dataclass(frozen=True)
class CommitResult:
    """Outcome of a commit handler invocation."""

    ok: bool
    data: Any = None
    error: str | None = None

    @staticmethod
    def success(data: Any = None) -> CommitResult:
        return CommitResult(ok=True, data=data)

    @staticmethod
    def failure(message: str) -> CommitResult:
        return CommitResult(ok=False, error=message)


@dataclass
class CommitContext:
    """Payload passed to commit handlers."""

    wizard_name: str
    state: BaseState
    answers: dict[str, Any]
    hook_name: str
    resource_engine: ResourceEngine | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def fetch_resource(self, provider_name: str, resource_id: str, **params: Any) -> Any:
        """Helper for handlers that need ``ResourceEngine`` access."""
        if self.resource_engine is None:
            raise RuntimeError("ResourceEngine is not configured for this commit")
        provider = self.resource_engine.use(provider_name)
        return provider.fetch(resource_id, **params)


class CommitRegistry:
    """Register named commit handlers (code-defined)."""

    def __init__(self) -> None:
        self._handlers: dict[str, CommitHandler] = {}

    def register(self, name: str, handler: CommitHandler) -> None:
        if not name:
            raise ValueError("Commit handler name must be non-empty")
        self._handlers[name] = handler

    def has(self, name: str) -> bool:
        return name in self._handlers

    def run(self, name: str, context: CommitContext) -> CommitResult:
        handler = self._handlers.get(name)
        if handler is None:
            return CommitResult.failure(f"Unknown commit handler: {name!r}")
        try:
            return handler(context)
        except Exception as exc:
            return CommitResult.failure(str(exc))


_default_commit_registry = CommitRegistry()


def default_commit_registry() -> CommitRegistry:
    return _default_commit_registry