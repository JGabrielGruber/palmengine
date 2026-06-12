"""
State scope management — nested dictionaries with legacy flat-key fallback.

Scoped values live under ``__palm:scopes`` as nested dicts when a state
instance opts into structured storage (typically when a schema is bound).
Legacy flat keys (``__palm:scope:{path}:{key}``) remain readable for backward
compatibility.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.exceptions import ContextError

SCOPES_ROOT_KEY = "__palm:scopes"
NESTED_SCOPES_KEY = "__scopes"
LEGACY_SCOPE_PREFIX = "__palm:scope:"
_RESERVED_SCOPE_KEYS = frozenset({NESTED_SCOPES_KEY})


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

    def get_nested(
        self,
        root: dict[str, Any],
        key: str,
        default: Any = None,
        *,
        legacy_get: Callable[[str, Any], Any] | None = None,
        legacy_has: Callable[[str], bool] | None = None,
    ) -> Any:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(root, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return node[key]
        if legacy_get is not None and legacy_has is not None:
            return self.get_legacy(key, default, get=legacy_get, has=legacy_has)
        return default

    def set_nested(self, root: dict[str, Any], key: str, value: Any) -> None:
        if not self._stack:
            raise ContextError("Cannot set scoped value without an active scope")
        node = self._navigate(root, self._stack, create=True)
        if node is None:
            raise ContextError("Cannot set scoped value without an active scope")
        node[key] = value

    def has_nested(
        self,
        root: dict[str, Any],
        key: str,
        *,
        legacy_has: Callable[[str], bool] | None = None,
    ) -> bool:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(root, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return True
        if legacy_has is not None:
            return self.has_legacy(key, has=legacy_has)
        return False

    def get_legacy(
        self,
        key: str,
        default: Any,
        *,
        get: Callable[[str, Any], Any],
        has: Callable[[str], bool],
    ) -> Any:
        for scope_path in reversed(self._scope_paths()):
            storage_key = legacy_storage_key(scope_path, key)
            if has(storage_key):
                return get(storage_key, default)
        return default

    def set_legacy(
        self,
        key: str,
        value: Any,
        *,
        set_value: Callable[[str, Any], None],
    ) -> None:
        scope_path = self._current_scope_path()
        if scope_path is None:
            raise ContextError("Cannot set scoped value without an active scope")
        set_value(legacy_storage_key(scope_path, key), value)

    def has_legacy(self, key: str, *, has: Callable[[str], bool]) -> bool:
        for scope_path in reversed(self._scope_paths()):
            if has(legacy_storage_key(scope_path, key)):
                return True
        return False

    def scoped_view(self, root: dict[str, Any]) -> dict[str, Any]:
        """Return a shallow copy of keys in the current nested scope."""
        if not self._stack:
            return {}
        node = self._navigate(root, self._stack, create=False)
        if node is None:
            return {}
        return {
            key: value
            for key, value in node.items()
            if key not in _RESERVED_SCOPE_KEYS
        }

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
    """Build a legacy flat storage key for backward compatibility."""
    return f"{LEGACY_SCOPE_PREFIX}{scope_path}:{key}"