"""
Behavior Tree engine — general-purpose control-flow execution.

Runs a tree rooted at ``BasePattern`` with pluggable ``BaseState``. Independent
of wizards, CLI, persistence, and other engines.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.behavior_tree.base_pattern import BasePattern, PatternStatus
from palm.core.behavior_tree.exceptions import BehaviorTreeError, NodeExecutionError
from palm.core.behavior_tree.root import RootNode
from palm.core.context import BaseState
from palm.core.exceptions import StateError, StateNotConfiguredError

_CONTINUING = frozenset({PatternStatus.RUNNING})


class BehaviorTreeEngine(BasePalmEngine):
    """
    Executes a behavior tree with pluggable execution state.

    Provide ``state`` at ``initialize`` (e.g. ``BlackboardState`` from
    ``palm.states``). Use ``set_root`` then ``tick`` or ``tick_until_terminal``.
    """

    def __init__(self) -> None:
        super().__init__(name="behavior_tree")
        self._root: BasePattern | None = None
        self._state: BaseState | None = None
        self._last_status = PatternStatus.FAILURE

    @property
    def state(self) -> BaseState:
        """The active execution state."""
        return self._require_state()

    @property
    def root(self) -> BasePattern | None:
        return self._root

    @property
    def last_status(self) -> PatternStatus:
        return self._last_status

    def set_root(self, root: BasePattern) -> None:
        """Assign the tree root. Validates structure when ``root`` is a ``RootNode``."""
        self._root = root
        if isinstance(root, RootNode):
            root.validate_tree_structure()

    def tick(self) -> PatternStatus:
        """Perform a single tree tick."""
        if self._root is None:
            self._last_status = PatternStatus.FAILURE
            return self._last_status
        try:
            self._last_status = self._root.tick(self._require_state())
            return self._last_status
        except NodeExecutionError:
            raise
        except StateError:
            raise
        except Exception as exc:
            raise BehaviorTreeError(
                f"Unexpected error during BehaviorTreeEngine.tick: {exc}"
            ) from exc

    def tick_until_terminal(self, max_ticks: int = 10_000) -> PatternStatus:
        """
        Tick until SUCCESS, FAILURE, or WAITING_FOR_INPUT.

        Raises ``BehaviorTreeError`` if ``max_ticks`` is exceeded while still RUNNING.
        """
        if max_ticks < 1:
            raise ValueError("max_ticks must be >= 1")

        for _ in range(max_ticks):
            status = self.tick()
            if status not in _CONTINUING:
                return status

        raise BehaviorTreeError(
            f"Tree did not reach a terminal state after {max_ticks} ticks. "
            f"Last status: {self._last_status}"
        )

    def reset(self) -> None:
        """Reset root subtree state and last status."""
        if self._root is not None and hasattr(self._root, "reset"):
            self._root.reset()
        self._last_status = PatternStatus.FAILURE

    def _require_state(self) -> BaseState:
        if self._state is None:
            raise StateNotConfiguredError(
                "No execution state is configured. Pass state= to initialize()."
            )
        return self._state

    def _do_initialize(self, **options: Any) -> None:
        state = options.get("state")
        if isinstance(state, BaseState):
            self._state = state

        root = options.get("root")
        if root is not None and isinstance(root, BasePattern):
            self.set_root(root)

    def _do_shutdown(self) -> None:
        self.reset()
        if self._state is not None:
            self._state.clear()
        self._state = None
        self._root = None
