"""
Behavior Tree engine — general-purpose control-flow execution.

Runs a tree rooted at ``BasePattern`` (typically ``RootNode``) with a shared
``Blackboard``. Independent of wizards, CLI, persistence, and other engines.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.behavior_tree.base_pattern import BasePattern, PatternStatus
from palm.core.behavior_tree.blackboard import Blackboard
from palm.core.behavior_tree.exceptions import BehaviorTreeError, NodeExecutionError
from palm.core.behavior_tree.root import RootNode

_CONTINUING = frozenset({PatternStatus.RUNNING})


class BehaviorTreeEngine(BasePalmEngine):
    """
    Executes a behavior tree with a shared blackboard.

    Set a root via ``set_root`` (``RootNode`` recommended), then drive execution
    with ``tick`` or ``tick_until_terminal``.
    """

    def __init__(self) -> None:
        super().__init__(name="behavior_tree")
        self._root: BasePattern | None = None
        self._blackboard = Blackboard()
        self._last_status = PatternStatus.FAILURE

    @property
    def blackboard(self) -> Blackboard:
        return self._blackboard

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
            self._last_status = self._root.tick(self._blackboard)
            return self._last_status
        except NodeExecutionError:
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

    def _do_initialize(self, **options: Any) -> None:
        initial = options.get("blackboard")
        if isinstance(initial, Blackboard):
            self._blackboard = initial
        elif isinstance(initial, dict):
            self._blackboard = Blackboard(initial)

        root = options.get("root")
        if root is not None and isinstance(root, BasePattern):
            self.set_root(root)

    def _do_shutdown(self) -> None:
        self.reset()
        self._blackboard.clear()
        self._root = None