"""
Test doubles for core engine tests.

State fakes: :class:`TestState`
Orchestration fakes: :class:`TestMode`, :class:`TestRunner`
Behavior-tree fakes: :class:`FakePattern`, :class:`StubInteractiveLeaf`
Utility fakes: :class:`FakeScheduler`
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.behavior_tree import BasePattern, InteractiveLeaf, PatternStatus
from palm.core.context import BaseState
from tests.core.fakes.mode import TestMode
from tests.core.fakes.runner import TestRunner
from tests.core.fakes.state import TestState


class FakePattern(BasePattern):
    """Minimal pattern with a fixed or callable tick outcome."""

    def __init__(
        self,
        name: str = "fake",
        *,
        status: PatternStatus = PatternStatus.SUCCESS,
        on_tick: Callable[[BaseState], PatternStatus] | None = None,
    ) -> None:
        self.name = name
        self._status = status
        self._on_tick = on_tick
        self.tick_count = 0

    def tick(self, state: BaseState) -> PatternStatus:
        self.tick_count += 1
        if self._on_tick is not None:
            return self._on_tick(state)
        return self._status


class FakeScheduler:
    """Records scheduled callbacks for orchestration and runtime tests."""

    def __init__(self) -> None:
        self.tasks: list[tuple[str, Any]] = []

    def schedule(self, name: str, payload: Any = None) -> None:
        self.tasks.append((name, payload))

    def clear(self) -> None:
        self.tasks.clear()


class FakeInputCapable:
    """Minimal :class:`~palm.core.orchestration.input_capable.InputCapable` double."""

    def __init__(self, *, step: str = "ask") -> None:
        self.step = step
        self.values: list[Any] = []

    def provide_input(self, state: BaseState, value: Any) -> str | None:
        self.values.append(value)
        state.set("__input__", value)
        return self.step

    def current_step_slug(self, state: BaseState) -> str | None:
        return self.step

    def answers(self, state: BaseState) -> dict[str, Any]:
        value = state.get("__input__")
        return {} if value is None else {"last": value}


class StubInteractiveLeaf(InteractiveLeaf):
    """Stub implementation for testing the interactive leaf contract."""

    def __init__(self, name: str = "test_interactive") -> None:
        super().__init__(name)
        self.received_value: Any = None

    def _request_input(self, state: BaseState) -> PatternStatus:
        state.set(self.prompt_key(), {"message": "Please provide input"})
        return PatternStatus.WAITING_FOR_INPUT

    def _handle_input(self, value: Any, state: BaseState) -> PatternStatus:
        self.received_value = value
        state.set(f"__test_received__:{self.name}", value)
        return PatternStatus.SUCCESS


__all__ = [
    "FakeInputCapable",
    "FakePattern",
    "FakeScheduler",
    "StubInteractiveLeaf",
    "TestMode",
    "TestRunner",
    "TestState",
]