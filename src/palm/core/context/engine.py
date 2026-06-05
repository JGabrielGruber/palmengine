"""
Context engine — stack-based scoped execution context.

Runtimes and patterns attach session-local metadata to named context frames
without coupling to CLI or persistence.
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.exceptions import ContextError


class ContextEngine(BasePalmEngine):
    """Maintains a stack of named execution contexts with push/pop semantics."""

    _ROOT_KEY = "_name"

    def __init__(self) -> None:
        super().__init__(name="context")
        self._stack: list[dict[str, Any]] = [self._make_frame("root")]

    @property
    def current(self) -> dict[str, Any]:
        """The active context frame (mutable)."""
        return self._stack[-1]

    @property
    def depth(self) -> int:
        """Number of frames on the stack (including root)."""
        return len(self._stack)

    @property
    def current_name(self) -> str:
        return str(self.current.get(self._ROOT_KEY, "root"))

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value from the current frame."""
        return self.current.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Write a value into the current frame."""
        self.current[key] = value

    def push(self, name: str, **data: Any) -> dict[str, Any]:
        """
        Push a new named context frame onto the stack.

        Returns the new frame dict for direct mutation.
        """
        frame = self._make_frame(name, **data)
        self._stack.append(frame)
        return frame

    def pop(self) -> dict[str, Any]:
        """
        Pop the current frame.

        The root frame cannot be popped.
        """
        if len(self._stack) <= 1:
            raise ContextError("Cannot pop the root context frame")
        return self._stack.pop()

    @contextmanager
    def scope(self, name: str, **data: Any) -> Generator[dict[str, Any], None, None]:
        """Context manager wrapping ``push`` / ``pop``."""
        frame = self.push(name, **data)
        try:
            yield frame
        finally:
            self.pop()

    def frames(self) -> tuple[Mapping[str, Any], ...]:
        """Immutable snapshot of all frames (shallow copies)."""
        return tuple(dict(frame) for frame in self._stack)

    def _make_frame(self, name: str, **data: Any) -> dict[str, Any]:
        return {self._ROOT_KEY: name, **data}

    def _do_initialize(self, **options: Any) -> None:
        seed = options.get("initial")
        if isinstance(seed, dict):
            self._stack = [self._make_frame("root", **seed)]
        else:
            self._stack = [self._make_frame("root")]

    def _do_shutdown(self) -> None:
        self._stack = [self._make_frame("root")]