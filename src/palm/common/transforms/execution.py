"""
High-level transform execution helpers for patterns and runtimes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from palm.core.context.base_state import BaseState
from palm.core.transform.base import TransformResult
from palm.core.transform.engine import TransformEngine


class TransformExecutor:
    """
    Thin coordinator around :class:`~palm.core.transform.engine.TransformEngine`.

    Ensures common rules are loaded and the engine is initialized before use.
    Patterns may share one executor instance or supply their own engine.
    """

    def __init__(self, engine: TransformEngine | None = None) -> None:
        self._engine = engine if engine is not None else TransformEngine()

    @property
    def engine(self) -> TransformEngine:
        """Return the underlying engine after ensuring readiness."""
        return self.ensure_ready()

    def ensure_ready(self) -> TransformEngine:
        """Load common rules and initialize the engine when needed."""
        from palm.common.transforms._apps import autoload

        autoload()
        if not self._engine.is_initialized:
            self._engine.initialize()
        return self._engine

    def apply(self, name: str, value: Any, **options: Any) -> TransformResult:
        """Apply one registered rule to ``value``."""
        return self.engine.apply(name, value, **options)

    def apply_chain(
        self,
        names: Sequence[str],
        value: Any,
        *,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
        **shared_options: Any,
    ) -> TransformResult:
        """Apply an ordered list of rules to ``value``."""
        return self.engine.apply_chain(
            names,
            value,
            options_by_rule=options_by_rule,
            **shared_options,
        )

    def apply_to_state(
        self,
        name: str,
        state: BaseState,
        source_key: str,
        **options: Any,
    ) -> TransformResult | None:
        """Read from state, transform, and write back."""
        return self.engine.apply_to_state(name, state, source_key, **options)

    def apply_chain_to_state(
        self,
        names: Sequence[str],
        state: BaseState,
        source_key: str,
        **options: Any,
    ) -> TransformResult | None:
        """Read from state, run a rule chain, and write back."""
        return self.engine.apply_chain_to_state(names, state, source_key, **options)

    def apply_batch_to_state(
        self,
        name: str,
        state: BaseState,
        source_key: str,
        **options: Any,
    ) -> TransformResult | None:
        """Read a list from state, transform it, and write back."""
        return self.engine.apply_batch_to_state(name, state, source_key, **options)


_default_executor: TransformExecutor | None = None


def default_executor() -> TransformExecutor:
    """Return a process-wide lazy :class:`TransformExecutor`."""
    global _default_executor
    if _default_executor is None:
        _default_executor = TransformExecutor()
    return _default_executor


def apply_transform(name: str, value: Any, **options: Any) -> TransformResult:
    """Apply a registered rule using the default executor."""
    return default_executor().apply(name, value, **options)


def apply_transform_to_state(
    name: str,
    state: BaseState,
    source_key: str,
    **options: Any,
) -> TransformResult | None:
    """Apply a registered rule against state using the default executor."""
    return default_executor().apply_to_state(name, state, source_key, **options)
