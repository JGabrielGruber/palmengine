"""
State scope management — nested dictionaries with optional legacy flat-key reads.

Nested scopes are the default for dict-backed state (``scope_storage()``).
Legacy flat keys (``__palm:scope:{path}:{key}``) are read as a fallback when
nested lookups miss, so older persisted data remains accessible.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from palm.core.exceptions import ContextError

SCOPES_ROOT_KEY = "__palm:scopes"
NESTED_SCOPES_KEY = "__scopes"
LEGACY_SCOPE_PREFIX = "__palm:scope:"
_RESERVED_SCOPE_KEYS = frozenset({NESTED_SCOPES_KEY})


class ScopeStorageMode(Enum):
    """How scoped values are written for a state instance."""

    NESTED = "nested"
    LEGACY = "legacy"


class StateScopeManager:
    """Stack-based scope coordinator for dict-backed state storage."""

    def __init__(self, scope_stack: list[str]) -> None:
        self._stack = scope_stack

    def enter(self, name: str) -> str:
        if not name:
            raise ContextError("State scope name cannot be empty")
        self._stack.append(name)
        return name

    def exit(self) -> str:
        if not self._stack:
            raise ContextError("Cannot exit state scope: stack is empty")
        return self._stack.pop()

    def current(self) -> str | None:
        if not self._stack:
            return None
        return self._stack[-1]

    def depth(self) -> int:
        return len(self._stack)

    def get(
        self,
        key: str,
        default: Any,
        *,
        mode: ScopeStorageMode,
        storage: dict[str, Any] | None,
        get_value: Callable[[str, Any], Any],
        has_key: Callable[[str], bool],
    ) -> Any:
        if mode is ScopeStorageMode.NESTED and storage is not None:
            return self._get_nested(
                storage,
                key,
                default,
                get_value=get_value,
                has_key=has_key,
            )
        return self._get_legacy(key, default, get_value=get_value, has_key=has_key)

    def set(
        self,
        key: str,
        value: Any,
        *,
        mode: ScopeStorageMode,
        storage: dict[str, Any] | None,
        set_value: Callable[[str, Any], None],
    ) -> None:
        if not self._stack:
            raise ContextError("Cannot set scoped value without an active scope")
        if mode is ScopeStorageMode.NESTED and storage is not None:
            self._set_nested(storage, key, value)
            return
        scope_path = self._current_scope_path()
        if scope_path is None:
            raise ContextError("Cannot set scoped value without an active scope")
        set_value(legacy_storage_key(scope_path, key), value)

    def contains(
        self,
        key: str,
        *,
        mode: ScopeStorageMode,
        storage: dict[str, Any] | None,
        has_key: Callable[[str], bool],
    ) -> bool:
        if mode is ScopeStorageMode.NESTED and storage is not None:
            return self._has_nested(storage, key, has_key=has_key)
        return self._has_legacy(key, has_key=has_key)

    def view(self, storage: dict[str, Any]) -> dict[str, Any]:
        """Return a shallow copy of keys in the current nested scope."""
        if not self._stack:
            return {}
        node = self._navigate(storage, self._stack, create=False)
        if node is None:
            return {}
        return {
            key: value
            for key, value in node.items()
            if key not in _RESERVED_SCOPE_KEYS
        }

    def _get_nested(
        self,
        storage: dict[str, Any],
        key: str,
        default: Any,
        *,
        get_value: Callable[[str, Any], Any],
        has_key: Callable[[str], bool],
    ) -> Any:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(storage, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return node[key]
        return self._get_legacy(key, default, get_value=get_value, has_key=has_key)

    def _set_nested(self, storage: dict[str, Any], key: str, value: Any) -> None:
        node = self._navigate(storage, self._stack, create=True)
        if node is None:
            raise ContextError("Cannot set scoped value without an active scope")
        node[key] = value

    def _has_nested(
        self,
        storage: dict[str, Any],
        key: str,
        *,
        has_key: Callable[[str], bool],
    ) -> bool:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(storage, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return True
        return self._has_legacy(key, has_key=has_key)

    def _get_legacy(
        self,
        key: str,
        default: Any,
        *,
        get_value: Callable[[str, Any], Any],
        has_key: Callable[[str], bool],
    ) -> Any:
        for scope_path in reversed(self._scope_paths()):
            storage_key = legacy_storage_key(scope_path, key)
            if has_key(storage_key):
                return get_value(storage_key, default)
        return default

    def _has_legacy(self, key: str, *, has_key: Callable[[str], bool]) -> bool:
        for scope_path in reversed(self._scope_paths()):
            if has_key(legacy_storage_key(scope_path, key)):
                return True
        return False

    def _current_scope_path(self) -> str | None:
        if not self._stack:
            return None
        return ".".join(self._stack)

    def _scope_paths(self) -> list[str]:
        if not self._stack:
            return []
        return [".".join(self._stack[: index + 1]) for index in range(len(self._stack))]

    def _navigate(
        self,
        root: dict[str, Any],
        stack: list[str],
        *,
        create: bool,
    ) -> dict[str, Any] | None:
        if not stack:
            return None

        scopes_root = root.get(SCOPES_ROOT_KEY)
        if scopes_root is None:
            if not create:
                return None
            scopes_root = {}
            root[SCOPES_ROOT_KEY] = scopes_root
        if not isinstance(scopes_root, dict):
            if not create:
                return None
            scopes_root = {}
            root[SCOPES_ROOT_KEY] = scopes_root

        current: dict[str, Any] = scopes_root
        for index, name in enumerate(stack):
            if name not in current:
                if not create:
                    return None
                current[name] = {}
            node = current[name]
            if not isinstance(node, dict):
                if not create:
                    return None
                node = {}
                current[name] = node
            if index == len(stack) - 1:
                return node
            children = node.get(NESTED_SCOPES_KEY)
            if children is None:
                if not create:
                    return None
                children = {}
                node[NESTED_SCOPES_KEY] = children
            if not isinstance(children, dict):
                if not create:
                    return None
                children = {}
                node[NESTED_SCOPES_KEY] = children
            current = children
        return None


def legacy_storage_key(scope_path: str, key: str) -> str:
    """Build a legacy flat storage key for backward-compatible reads."""
    return f"{LEGACY_SCOPE_PREFIX}{scope_path}:{key}"