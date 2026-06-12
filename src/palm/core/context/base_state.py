"""
Abstract execution state for behavior trees and context frames.

Engines and nodes depend only on ``BaseState``. Concrete implementations
(dict-backed blackboard, scoped test doubles, etc.) live outside ``palm.core``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from palm.core.context.scoping import StateScopeManager
from palm.core.exceptions import StateValidationError

if TYPE_CHECKING:
    from palm.core.context.state_schema import StateSchema


class BaseState(ABC):
    """Pluggable key-value state surface shared across ticks and context scopes."""

    def __init__(self, *, schema: StateSchema | None = None) -> None:
        self._schema = schema
        self._scope_stack: list[str] = []
        self._scope_manager = StateScopeManager(self._scope_stack)

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
        return self._scope_manager.enter(name)

    def exit_scope(self) -> str:
        """Pop the innermost state scope. Raises if the stack is empty."""
        self._ensure_extensions()
        return self._scope_manager.exit()

    @contextmanager
    def scope(self, name: str) -> Generator[BaseState, None, None]:
        """Enter a named scope for the duration of the ``with`` block."""
        self.enter_scope(name)
        try:
            yield self
        finally:
            self.exit_scope()

    def current_scope(self) -> str | None:
        """Return the active scope name, or ``None`` at the root."""
        self._ensure_extensions()
        return self._scope_manager.current()

    def scope_depth(self) -> int:
        """Return the number of nested state scopes."""
        self._ensure_extensions()
        return self._scope_manager.depth()

    def scoped_keys(self) -> list[str]:
        """Return keys visible in the current scope (nested mode only)."""
        root = self._scope_root()
        if root is None:
            return []
        return list(self._scope_manager.scoped_view(root).keys())

    def get_scoped(self, key: str, default: Any = None) -> Any:
        """Resolve ``key`` within the current scope, then parent scopes."""
        self._ensure_extensions()
        root = self._scope_root()
        if root is not None:
            return self._scope_manager.get_nested(
                root,
                key,
                default,
                legacy_get=self.get,
                legacy_has=self.has,
            )
        return self._scope_manager.get_legacy(key, default, get=self.get, has=self.has)

    def set_scoped(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the current scope."""
        self._ensure_extensions()
        root = self._scope_root()
        if root is not None:
            self._scope_manager.set_nested(root, key, value)
            return
        self._scope_manager.set_legacy(key, value, set_value=self.set)

    def has_scoped(self, key: str) -> bool:
        """Return whether ``key`` exists in the current or parent scopes."""
        self._ensure_extensions()
        root = self._scope_root()
        if root is not None:
            return self._scope_manager.has_nested(
                root,
                key,
                legacy_has=self.has,
            )
        return self._scope_manager.has_legacy(key, has=self.has)

    def _scope_root(self) -> dict[str, Any] | None:
        """Return mutable storage for nested scopes, or ``None`` for legacy mode."""
        return None

    def _ensure_extensions(self) -> None:
        """Initialize schema/scoping attributes for legacy subclasses."""
        if not hasattr(self, "_scope_stack"):
            self._scope_stack = []
        if not hasattr(self, "_schema"):
            self._schema = None
        if not hasattr(self, "_scope_manager"):
            self._scope_manager = StateScopeManager(self._scope_stack)