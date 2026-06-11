"""
TransformLeaf — behavior-tree leaf that applies transform rules to blackboard data.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState
from palm.core.transform.engine import TransformEngine


class TransformLeaf(LeafNode):
    """
    Read a value from ``source_key``, transform it, and write to ``target_key``.

    Supports a single ``rule``, an ordered ``chain`` of rules, and batch mode
    when the source value is a list (or ``batch=True``). A trace dict is stored
    at ``trace_key()`` for audit and lens-style debugging.
    """

    TRACE_KEY_PREFIX = "__bt_transform__"

    def __init__(
        self,
        name: str,
        *,
        engine: TransformEngine,
        source_key: str,
        target_key: str,
        rule: str | None = None,
        chain: Sequence[str] | None = None,
        batch: bool = False,
        options: dict[str, Any] | None = None,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(name)
        if not rule and not chain:
            raise ValueError("TransformLeaf requires rule or chain")
        if rule and chain:
            raise ValueError("TransformLeaf accepts rule or chain, not both")
        self._engine = engine
        self._source_key = source_key
        self._target_key = target_key
        self._rule = rule
        self._chain = list(chain) if chain is not None else None
        self._batch = batch
        self._options = dict(options or {})
        self._options_by_rule = dict(options_by_rule or {})

    def trace_key(self) -> str:
        return f"{self.TRACE_KEY_PREFIX}:{self.name}"

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        if not self._engine.is_initialized:
            self._engine.initialize()

        raw = state.get(self._source_key)
        if raw is None:
            return PatternStatus.FAILURE

        if self._batch or isinstance(raw, list):
            contexts = self._run_batch(raw)
            state.set(self._target_key, [ctx.value for ctx in contexts])
            state.set(
                self.trace_key(),
                {"mode": "batch", "items": [ctx.to_trace() for ctx in contexts]},
            )
            return PatternStatus.SUCCESS

        context = self._run_single(raw)
        state.set(self._target_key, context.value)
        state.set(self.trace_key(), context.to_trace())
        return PatternStatus.SUCCESS

    def _run_single(self, value: Any) -> Any:
        if self._chain is not None:
            return self._engine.apply_chain(
                self._chain,
                value,
                options_by_rule=self._options_by_rule,
                **self._options,
            )
        return self._engine.apply_auto(self._rule or "", value, **self._options)

    def _run_batch(self, items: Sequence[Any]) -> list[Any]:
        if self._chain is not None:
            return [
                self._engine.apply_chain(
                    self._chain,
                    item,
                    options_by_rule=self._options_by_rule,
                    **self._options,
                )
                for item in items
            ]
        return self._engine.apply_batch(self._rule or "", items, **self._options)