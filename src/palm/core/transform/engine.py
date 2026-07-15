"""
Transform engine — resolve and apply registered transformation rules.

Supports single-value transforms, batch list processing, chained pipelines,
and native :class:`~palm.core.context.BaseState` reads and writes with
scope and schema awareness.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.context.base_state import BaseState
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import (
    BaseTransformRule,
    TransformContext,
    TransformMode,
    TransformResult,
)
from palm.core.transform.registry import transform_registry

_MISSING = object()


class TransformEngine(BasePalmEngine):
    """
    Coordinates transformation rules by name.

    Supports single-value transforms, batch list processing, and chained pipelines
    with :class:`TransformContext` preserving original and intermediate views.
    State-aware helpers read from and write to :class:`BaseState` using scoped
    or root keys and optional schema validation on output.
    """

    def __init__(self) -> None:
        super().__init__(name="transform")

    def resolve(self, name: str, **options: Any) -> BaseTransformRule:
        """Instantiate a registered transform rule."""
        cls = transform_registry.get(name)
        build_options = {key: value for key, value in options.items() if not key.startswith("_")}
        return cls.from_options(**build_options)

    def apply(
        self,
        name: str,
        value: Any,
        *,
        state: BaseState | None = None,
        **options: Any,
    ) -> TransformResult:
        """Apply one rule to ``value`` and return the resulting context."""
        context = TransformContext(original=value, state=state)
        rule = self.resolve(name, **options)
        advanced = self._apply_rule(rule, context, **options)
        return TransformResult(context=advanced)

    def apply_chain(
        self,
        names: Sequence[str],
        value: Any,
        *,
        state: BaseState | None = None,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
        **shared_options: Any,
    ) -> TransformResult:
        """Apply rules in order, threading the context forward."""
        context = TransformContext(original=value, state=state)
        rule_options = options_by_rule or {}
        for rule_name in names:
            merged = {**shared_options, **rule_options.get(rule_name, {})}
            rule = self.resolve(rule_name, **merged)
            context = self._apply_rule(rule, context, **merged)
        return TransformResult(context=context)

    def apply_batch(
        self,
        name: str,
        items: Sequence[Any],
        *,
        state: BaseState | None = None,
        **options: Any,
    ) -> list[TransformResult]:
        """Apply a rule independently to each item."""
        rule = self.resolve(name, **options)
        results: list[TransformResult] = []
        for item in items:
            context = TransformContext(original=item, state=state)
            advanced = self._apply_rule(rule, context, **options)
            results.append(TransformResult(context=advanced))
        return results

    def apply_auto(
        self,
        name: str,
        value: Any,
        *,
        state: BaseState | None = None,
        **options: Any,
    ) -> TransformResult:
        """
        Apply a rule using its declared mode.

        ``BATCH`` rules receive the whole list; ``SINGLE`` rules receive the scalar;
        ``AUTO`` detects lists and delegates to batch or single accordingly.
        """
        rule = self.resolve(name, **options)
        if rule.mode is TransformMode.BATCH:
            context = TransformContext(original=value, state=state)
            advanced = self._apply_rule(rule, context, **options)
            return TransformResult(context=advanced)
        if rule.mode is TransformMode.AUTO and isinstance(value, list):
            context = TransformContext(original=value, state=state)
            advanced = self._apply_rule(rule, context, **options)
            return TransformResult(context=advanced)
        return self.apply(name, value, state=state, **options)

    def read_state_value(
        self,
        state: BaseState,
        key: str,
        *,
        scoped: bool = False,
        default: Any = _MISSING,
    ) -> Any:
        """Read ``key`` from ``state``, optionally using scoped resolution."""
        if scoped and state.current_scope() is not None:
            if default is _MISSING:
                return state.get_scoped(key)
            return state.get_scoped(key, default)
        if default is _MISSING:
            return state.get(key)
        return state.get(key, default)

    def write_state_value(
        self,
        state: BaseState,
        key: str,
        value: Any,
        *,
        scoped: bool = False,
        validate: bool = True,
    ) -> None:
        """Write ``value`` under ``key`` with optional schema validation."""
        if scoped and state.current_scope() is not None:
            if validate:
                schema = state.effective_schema()
                if schema is not None:
                    schema.validate_key(key, value)
            state.set_scoped(key, value)
            return
        if validate:
            state.set_validated(key, value)
        else:
            state.set(key, value)

    def apply_to_state(
        self,
        name: str,
        state: BaseState,
        source_key: str,
        *,
        target_key: str | None = None,
        scoped: bool = False,
        validate_output: bool = True,
        skip_if_missing: bool = False,
        trace_key: str | None = None,
        **options: Any,
    ) -> TransformResult | None:
        """
        Read from ``source_key``, transform, and write to ``target_key``.

        Returns ``None`` when ``skip_if_missing`` is true and the source is absent.
        """
        raw = self.read_state_value(state, source_key, scoped=scoped, default=_MISSING)
        if raw is _MISSING or raw is None:
            if skip_if_missing:
                return None
            raise TransformApplicationError(
                f"Source key {source_key!r} is missing or null",
            )

        destination = target_key or source_key
        rule_options = {**options, "_target_key": destination}
        result = self.apply_auto(name, raw, state=state, **rule_options)
        writes: list[tuple[str, Any]] = [(destination, result.value)]
        self.write_state_value(
            state,
            destination,
            result.value,
            scoped=scoped,
            validate=validate_output,
        )
        if trace_key is not None:
            self.write_state_value(
                state,
                trace_key,
                result.context.to_trace(),
                scoped=scoped,
                validate=False,
            )
            writes.append((trace_key, result.context.to_trace()))

        return TransformResult(context=result.context, state_writes=tuple(writes))

    def apply_chain_to_state(
        self,
        names: Sequence[str],
        state: BaseState,
        source_key: str,
        *,
        target_key: str | None = None,
        scoped: bool = False,
        validate_output: bool = True,
        skip_if_missing: bool = False,
        trace_key: str | None = None,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
        **shared_options: Any,
    ) -> TransformResult | None:
        """Read from state, apply a rule chain, and write the final value."""
        raw = self.read_state_value(state, source_key, scoped=scoped, default=_MISSING)
        if raw is _MISSING or raw is None:
            if skip_if_missing:
                return None
            raise TransformApplicationError(
                f"Source key {source_key!r} is missing or null",
            )

        destination = target_key or source_key
        chain_options = {**shared_options, "_target_key": destination}
        result = self.apply_chain(
            names,
            raw,
            state=state,
            options_by_rule=options_by_rule,
            **chain_options,
        )
        writes: list[tuple[str, Any]] = [(destination, result.value)]
        self.write_state_value(
            state,
            destination,
            result.value,
            scoped=scoped,
            validate=validate_output,
        )
        if trace_key is not None:
            self.write_state_value(
                state,
                trace_key,
                result.context.to_trace(),
                scoped=scoped,
                validate=False,
            )
            writes.append((trace_key, result.context.to_trace()))

        return TransformResult(context=result.context, state_writes=tuple(writes))

    def apply_batch_to_state(
        self,
        name: str,
        state: BaseState,
        source_key: str,
        *,
        target_key: str | None = None,
        scoped: bool = False,
        validate_output: bool = True,
        skip_if_missing: bool = False,
        per_item: bool | None = None,
        trace_key: str | None = None,
        **options: Any,
    ) -> TransformResult | None:
        """
        Read a list from state, transform it, and write results back.

        When ``per_item`` is ``None``, batch-mode rules process the whole list;
        single-mode rules map independently over each element.
        """
        raw = self.read_state_value(state, source_key, scoped=scoped, default=_MISSING)
        if raw is _MISSING or raw is None:
            if skip_if_missing:
                return None
            raise TransformApplicationError(
                f"Source key {source_key!r} is missing or null",
            )

        rule = self.resolve(name, **options)
        use_per_item = per_item
        if use_per_item is None:
            use_per_item = rule.mode is TransformMode.SINGLE

        if use_per_item:
            if not isinstance(raw, list):
                raise TransformApplicationError(
                    f"Per-item batch requires a list at {source_key!r}, "
                    f"got {type(raw).__name__}",
                )
            batch_results = self.apply_batch(name, raw, state=state, **options)
            output = [item.value for item in batch_results]
            context = TransformContext(original=raw, state=state).advance(
                rule.rule_name,
                output,
                meta={"mode": "per_item"},
            )
        else:
            auto_result = self.apply_auto(name, raw, state=state, **options)
            output = auto_result.value
            context = auto_result.context

        destination = target_key or source_key
        writes: list[tuple[str, Any]] = [(destination, output)]
        self.write_state_value(
            state,
            destination,
            output,
            scoped=scoped,
            validate=validate_output,
        )
        if trace_key is not None:
            trace = context.to_trace()
            self.write_state_value(
                state,
                trace_key,
                trace,
                scoped=scoped,
                validate=False,
            )
            writes.append((trace_key, trace))

        return TransformResult(context=context, state_writes=tuple(writes))

    def _apply_rule(
        self,
        rule: BaseTransformRule,
        context: TransformContext,
        **options: Any,
    ) -> TransformContext:
        if not rule.supports(context.value):
            raise TransformApplicationError(
                f"Transform {rule.rule_name!r} does not support " f"{type(context.value).__name__}",
            )
        runtime_options = {**options, "_engine": self}
        return rule.apply(context, **runtime_options)

    def _do_initialize(self, **options: Any) -> None:
        pass

    def _do_shutdown(self) -> None:
        pass
