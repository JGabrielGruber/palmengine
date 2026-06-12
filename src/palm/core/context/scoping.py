"""
State scope management — nested dictionaries under ``__palm:scopes``.
"""

from __future__ import annotations

from typing import Any

from palm.core.exceptions import ContextError

SCOPES_ROOT_KEY = "__palm:scopes"
NESTED_SCOPES_KEY = "__scopes"
_RESERVED_SCOPE_KEYS = frozenset({NESTED_SCOPES_KEY})


class StateScopeManager:
    """Stack-based scope coordinator for nested dict-backed state storage."""

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

    def get(self, storage: dict[str, Any], key: str, default: Any) -> Any:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(storage, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return node[key]
        return default

    def set(self, storage: dict[str, Any], key: str, value: Any) -> None:
        if not self._stack:
            raise ContextError("Cannot set scoped value without an active scope")
        node = self._navigate(storage, self._stack, create=True)
        if node is None:
            raise ContextError("Cannot set scoped value without an active scope")
        node[key] = value

    def contains(self, storage: dict[str, Any], key: str) -> bool:
        for depth in range(len(self._stack), 0, -1):
            node = self._navigate(storage, self._stack[:depth], create=False)
            if node is not None and key in node and key not in _RESERVED_SCOPE_KEYS:
                return True
        return False

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