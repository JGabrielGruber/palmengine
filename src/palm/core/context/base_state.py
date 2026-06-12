"""
Abstract execution state for behavior trees and context frames.

Engines and nodes depend only on ``BaseState``. Concrete implementations
(dict-backed blackboard, scoped test doubles, etc.) live outside ``palm.core``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from palm.core.context.observers import StateChangeObserver
from palm.core.context.scoping import StateScopeManager
from palm.core.exceptions import ContextError, StateValidationError

if TYPE_CHECKING:
    from palm.core.context.state_schema import StateSchema


class BaseState(ABC):
    """Pluggable key-value state surface shared across ticks and context scopes."""

    def __init__(self, *, schema: StateSchema | None = None) -> None:
        self._schema = schema
        self._scope_stack: list[str] = []
        self._scope_schemas: dict[str, StateSchema] = {}
        self._scope_manager = StateScopeManager(self._scope_stack)
        self._observer: StateChangeObserver | None = None

    @property
    def schema(self) -> StateSchema | None:
        """Return the optional schema bound to this state instance."""
        return getattr(self, "_schema", None)

    def bind_schema(self, schema: StateSchema | None) -> None:
        """Attach or replace the schema used for validation and defaults."""
        self._ensure_extensions()
        self._schema = schema
        self._notify_schema_bound(scope=None)

    def bind_scope_schema(self, scope_name: str, schema: StateSchema | None) -> None:
        """Attach a schema active when ``scope_name`` is on the scope stack."""
        self._ensure_extensions()
        if not scope_name:
            raise ContextError("Scope schema name cannot be empty")
        if schema is None:
            self._scope_schemas.pop(scope_name, None)
        else:
            self._scope_schemas[scope_name] = schema
        self._notify_schema_bound(scope=scope_name)

    def effective_schema(self) -> StateSchema | None:
        """Return the innermost schema for the active scope stack."""
        self._ensure_extensions()
        for name in reversed(self._scope_stack):
            scoped = self._scope_schemas.get(name)
            if scoped is not None:
                return scoped
        return self._schema

    def scope_schemas(self) -> dict[str, StateSchema]:
        """Return a copy of schemas bound to scope names."""
        self._ensure_extensions()
        return dict(self._scope_schemas)

    def restore_scope_schemas(self, schemas: Mapping[str, StateSchema]) -> None:
        """Replace per-scope schemas (used when resuming from snapshots)."""
        self._ensure_extensions()
        self._scope_schemas = dict(schemas)

    def set_observer(self, observer: StateChangeObserver | None) -> None:
        """Attach or remove a change observer."""
        self._observer = observer

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
        entered = self._scope_manager.enter(name)
        self._notify_scope_enter(entered)
        return entered

    def exit_scope(self) -> str:
        """Pop the innermost state scope. Raises if the stack is empty."""
        self._ensure_extensions()
        exited = self._scope_manager.exit()
        self._notify_scope_exit(exited)
        return exited

    def scope_stack(self) -> tuple[str, ...]:
        """Return the current scope stack from root to innermost."""
        self._ensure_extensions()
        return tuple(self._scope_stack)

    def restore_scope_stack(self, stack: Sequence[str]) -> None:
        """Replace the scope stack without firing observer notifications."""
        self._ensure_extensions()
        self._scope_stack.clear()
        self._scope_stack.extend(str(name) for name in stack)

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
        """Return keys visible in the current nested scope."""
        storage = self._require_scope_storage()
        return list(self._scope_manager.view(storage).keys())

    def get_scoped(self, key: str, default: Any = None) -> Any:
        """Resolve ``key`` within the current scope, then parent scopes."""
        self._ensure_extensions()
        return self._scope_manager.get(self._require_scope_storage(), key, default)

    def set_scoped(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the current scope."""
        self._ensure_extensions()
        self._scope_manager.set(self._require_scope_storage(), key, value)
        self._notify_value_set(key, value)

    def has_scoped(self, key: str) -> bool:
        """Return whether ``key`` exists in the current or parent scopes."""
        self._ensure_extensions()
        return self._scope_manager.contains(self._require_scope_storage(), key)

    def scope_storage(self) -> dict[str, Any] | None:
        """Return mutable backing storage for nested scopes."""
        return None

    def _require_scope_storage(self) -> dict[str, Any]:
        storage = self.scope_storage()
        if storage is None:
            raise ContextError("State does not support nested scope storage")
        return storage

    def _notify_value_set(self, key: str, value: Any) -> None:
        observer = getattr(self, "_observer", None)
        if observer is not None:
            observer.on_value_set(key, value, scope=self.current_scope())

    def _notify_scope_enter(self, name: str) -> None:
        observer = getattr(self, "_observer", None)
        if observer is not None:
            observer.on_scope_enter(name, stack=self.scope_stack())

    def _notify_scope_exit(self, name: str) -> None:
        observer = getattr(self, "_observer", None)
        if observer is not None:
            observer.on_scope_exit(name, stack=self.scope_stack())

    def _notify_schema_bound(self, *, scope: str | None) -> None:
        observer = getattr(self, "_observer", None)
        if observer is None:
            return
        schema = self._scope_schemas.get(scope) if scope else self._schema
        observer.on_schema_bound(schema, scope=scope)

    def _ensure_extensions(self) -> None:
        """Initialize schema/scoping attributes for legacy subclasses."""
        if not hasattr(self, "_scope_stack"):
            self._scope_stack = []
        if not hasattr(self, "_scope_schemas"):
            self._scope_schemas = {}
        if not hasattr(self, "_schema"):
            self._schema = None
        if not hasattr(self, "_scope_manager"):
            self._scope_manager = StateScopeManager(self._scope_stack)
        if not hasattr(self, "_observer"):
            self._observer = None