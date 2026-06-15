"""
TransformLeaf — apply registered transform rules to blackboard state.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from palm.core.behavior_tree.base_pattern import PatternStatus
from palm.core.behavior_tree.leaf import LeafNode
from palm.core.context import BaseState
from palm.core.exceptions import StateValidationError, TransformApplicationError, TransformError
from palm.core.transform.base import TransformContext, TransformMode, TransformResult
from palm.core.transform.engine import _MISSING, TransformEngine


class TransformLeaf(LeafNode):
    """
    Read a value from ``source_key``, transform it, and write to ``target_key``.

    Supports a single ``rule``, an ordered ``chain`` of rules, and batch mode.
    When ``batch`` is ``None`` (default), list inputs use per-item processing for
    single-mode rules and whole-list processing for batch-mode rules. Set
    ``batch=True`` or ``batch=False`` to override.

    Reads and writes respect ``scoped`` when a state scope is active. Output may
    be validated against :meth:`~palm.core.context.BaseState.effective_schema`.
    A trace dict is stored at ``trace_key`` (default: ``__bt_transform__:<name>``).
    Optional ``error_key`` receives a human-readable message on failure.
    """

    TRACE_KEY_PREFIX = "__bt_transform__"

    def __init__(
        self,
        name: str,
        *,
        engine: TransformEngine | None = None,
        source_key: str,
        target_key: str | None = None,
        rule: str | None = None,
        chain: Sequence[str] | None = None,
        scoped: bool = False,
        validate_output: bool = True,
        batch: bool | None = None,
        per_item: bool | None = None,
        options: dict[str, Any] | None = None,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
        skip_if_missing: bool = False,
        trace_key: str | None = None,
        error_key: str | None = None,
    ) -> None:
        super().__init__(name)
        if not source_key:
            raise ValueError(f"TransformLeaf {name!r} requires a non-empty source_key")
        if not rule and not chain:
            raise ValueError(
                f"TransformLeaf {name!r} requires rule or chain " f"(source_key={source_key!r})",
            )
        if rule and chain:
            raise ValueError(
                f"TransformLeaf {name!r} accepts rule or chain, not both "
                f"(rule={rule!r}, chain={list(chain)!r})",
            )
        self._engine = engine if engine is not None else TransformEngine()
        self._source_key = source_key
        self._target_key = target_key or source_key
        self._rule = rule
        self._chain = list(chain) if chain is not None else None
        self._scoped = scoped
        self._validate_output = validate_output
        self._batch = batch
        self._per_item = per_item
        self._options = dict(options or {})
        self._options_by_rule = dict(options_by_rule or {})
        self._skip_if_missing = skip_if_missing
        self._trace_key = trace_key if trace_key is not None else self.default_trace_key(name)
        self._error_key = error_key

    @staticmethod
    def default_trace_key(name: str) -> str:
        """Return the default audit key for a transform leaf."""
        return f"{TransformLeaf.TRACE_KEY_PREFIX}:{name}"

    @property
    def source_key(self) -> str:
        return self._source_key

    @property
    def target_key(self) -> str:
        return self._target_key

    @property
    def trace_key(self) -> str:
        return self._trace_key

    def _tick_impl(self, state: BaseState) -> PatternStatus:
        self._ensure_engine_ready()
        try:
            if self._should_use_batch(state):
                result = self._run_batch(state)
            else:
                result = self._run_single(state)
            if result is None:
                return PatternStatus.SUCCESS
            return PatternStatus.SUCCESS
        except (TransformApplicationError, TransformError, StateValidationError) as exc:
            return self._fail(state, str(exc))

    def _ensure_engine_ready(self) -> None:
        if not self._engine.is_initialized:
            self._engine.initialize()

    def _should_use_batch(self, state: BaseState) -> bool:
        if self._batch is True:
            return True
        if self._batch is False:
            return False
        raw = self._engine.read_state_value(
            state,
            self._source_key,
            scoped=self._scoped,
            default=None,
        )
        if not isinstance(raw, list):
            return False
        if self._chain is not None:
            return True
        if self._rule is None:
            return False
        resolved = self._engine.resolve(self._rule, **self._options)
        if self._per_item is not None:
            return self._per_item
        return resolved.mode is TransformMode.SINGLE

    def _run_single(self, state: BaseState) -> TransformResult | None:
        if self._chain is not None:
            return self._engine.apply_chain_to_state(
                self._chain,
                state,
                self._source_key,
                target_key=self._target_key,
                scoped=self._scoped,
                validate_output=self._validate_output,
                skip_if_missing=self._skip_if_missing,
                trace_key=self._trace_key,
                options_by_rule=self._options_by_rule,
                **self._options,
            )
        return self._engine.apply_to_state(
            self._rule or "",
            state,
            self._source_key,
            target_key=self._target_key,
            scoped=self._scoped,
            validate_output=self._validate_output,
            skip_if_missing=self._skip_if_missing,
            trace_key=self._trace_key,
            **self._options,
        )

    def _run_batch(self, state: BaseState) -> TransformResult | None:
        if self._chain is not None:
            return self._run_chain_per_item(state)
        return self._engine.apply_batch_to_state(
            self._rule or "",
            state,
            self._source_key,
            target_key=self._target_key,
            scoped=self._scoped,
            validate_output=self._validate_output,
            skip_if_missing=self._skip_if_missing,
            per_item=self._per_item if self._per_item is not None else True,
            trace_key=self._trace_key,
            **self._options,
        )

    def _run_chain_per_item(self, state: BaseState) -> TransformResult | None:
        raw = self._engine.read_state_value(
            state,
            self._source_key,
            scoped=self._scoped,
            default=_MISSING,
        )
        if raw is _MISSING or raw is None:
            if self._skip_if_missing:
                return None
            raise TransformApplicationError(
                f"Source key {self._source_key!r} is missing or null",
            )
        if not isinstance(raw, list):
            raise TransformApplicationError(
                f"Per-item chain requires a list at {self._source_key!r}, "
                f"got {type(raw).__name__}",
            )

        output: list[Any] = []
        traces: list[dict[str, Any]] = []
        for item in raw:
            result = self._engine.apply_chain(
                self._chain or [],
                item,
                state=state,
                options_by_rule=self._options_by_rule,
                **self._options,
            )
            output.append(result.value)
            traces.append(result.context.to_trace())

        context = TransformContext(original=raw, state=state).advance(
            self.name,
            output,
            meta={"mode": "chain_per_item", "count": len(output)},
        )
        self._engine.write_state_value(
            state,
            self._target_key,
            output,
            scoped=self._scoped,
            validate=self._validate_output,
        )
        batch_trace = {"mode": "chain_per_item", "items": traces, "value": output}
        self._engine.write_state_value(
            state,
            self._trace_key,
            batch_trace,
            scoped=self._scoped,
            validate=False,
        )
        return TransformResult(context=context)

    def _fail(self, state: BaseState, message: str) -> PatternStatus:
        detail = (
            f"Transform {self.name!r} failed for {self._source_key!r} "
            f"→ {self._target_key!r}: {message}"
        )
        if self._error_key:
            state.set(self._error_key, detail)
        return PatternStatus.FAILURE
