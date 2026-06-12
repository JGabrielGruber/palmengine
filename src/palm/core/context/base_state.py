"""
Abstract execution state for behavior trees and context frames.

Engines and nodes depend only on ``BaseState``. Concrete implementations
(dict-backed blackboard, scoped test doubles, etc.) live outside ``palm.core``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from palm.core.exceptions import ContextError, StateValidationError

if TYPE_CHECKING:
    from palm.core.context.state_schema import StateSchema

_SCOPE_PREFIX = "__palm:scope:"


class BaseState(ABC):
    """Pluggable key-value state surface shared across ticks and context scopes."""

    def __init__(self, *, schema: StateSchema | None = None) -> None:
        self._schema = schema
        self._scope_stack: list[str] = []

    @property
    def schema(self) -> StateSchema | None:
        """Return the optional schema bound to this state instance."""
        return getattr(self, "_schema", None)

    def bind_schema(self, schema: StateSchema | None) -> None:
        """Attach or replace the schema used for validation and defaults."""
        self._ensure_extensions()
        self._schema = schema

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for ``key``, or ``default`` if absent."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key``."""

    @abstractmethod
    def has(self, key: str) -> bool:
        """Return whether ``key`` exists."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove ``key`` if present."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries."""

    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of all entries."""

    @abstractmethod
    def keys(self) -> list[str]:
        """Return all current keys."""

    def validate(self) -> list[str]:
        """Validate the current snapshot against the bound schema."""
        self._ensure_extensions()
        if self._schema is None:
            return []
        return self._schema.validate_state(self.snapshot())

    def validate_key(self, key: str, value: Any | None = None) -> list[str]:
        """Validate one key, using ``value`` or the stored value when omitted."""
        self._ensure_extensions()
        if self._schema is None:
            return []
        candidate = self.get(key) if value is None else value
        if candidate is None and not self.has(key) and value is None:
            return []
        try:
            self._schema.validate_key(key, candidate)
        except StateValidationError as exc:
            return [str(exc)]
        return []

    def set_validated(self, key: str, value: Any) -> None:
        """Validate ``value`` for ``key`` and store it on success."""
        self._ensure_extensions()
        if self._schema is not None:
            self._schema.validate_key(key, value)
        self.set(key, value)

    def apply_defaults(self) -> None:
        """Apply schema defaults for keys that are not already present."""
        self._ensure_extensions()
        if self._schema is None:
            return
        for key, value in self._schema.defaults().items():
            if not self.has(key):
                self.set(key, value)

    def enter_scope(self, name: str) -> str:
        """Push ``name`` onto the state scope stack and return it."""
        self._ensure_extensions()
        if not name:
            raise ContextError("State scope name cannot be empty")
        self._scope_stack.append(name)
        return name

    def exit_scope(self) -> str:
        """Pop the innermost state scope. Raises if the stack is empty."""
        self._ensure_extensions()
        if not self._scope_stack:
            raise ContextError("Cannot exit state scope: stack is empty")
        return self._scope_stack.pop()

    def current_scope(self) -> str | None:
        """Return the active scope name, or ``None`` at the root."""
        self._ensure_extensions()
        if not self._scope_stack:
            return None
        return self._scope_stack[-1]

    def scope_depth(self) -> int:
        """Return the number of nested state scopes."""
        self._ensure_extensions()
        return len(self._scope_stack)

    def get_scoped(self, key: str, default: Any = None) -> Any:
        """Resolve ``key`` within the current scope, then parent scopes."""
        self._ensure_extensions()
        for scope_path in reversed(self._scope_paths()):
            storage_key = self._scoped_storage_key(scope_path, key)
            if self.has(storage_key):
                return self.get(storage_key)
        return default

    def set_scoped(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the current scope."""
        self._ensure_extensions()
        scope_path = self._current_scope_path()
        if scope_path is None:
            raise ContextError("Cannot set scoped value without an active scope")
        storage_key = self._scoped_storage_key(scope_path, key)
        self.set(storage_key, value)

    def has_scoped(self, key: str) -> bool:
        """Return whether ``key`` exists in the current or parent scopes."""
        self._ensure_extensions()
        for scope_path in reversed(self._scope_paths()):
            if self.has(self._scoped_storage_key(scope_path, key)):
                return True
        return False

    def _ensure_extensions(self) -> None:
        """Initialize schema/scoping attributes for legacy subclasses."""
        if not hasattr(self, "_scope_stack"):
            self._scope_stack = []
        if not hasattr(self, "_schema"):
            self._schema = None

    def _current_scope_path(self) -> str | None:
        if not self._scope_stack:
            return None
        return ".".join(self._scope_stack)

    def _scope_paths(self) -> list[str]:
        if not self._scope_stack:
            return []
        paths: list[str] = []
        for index in range(len(self._scope_stack)):
            paths.append(".".join(self._scope_stack[: index + 1]))
        return paths

    @staticmethod
    def _scoped_storage_key(scope_path: str, key: str) -> str:
        return f"{_SCOPE_PREFIX}{scope_path}:{key}"