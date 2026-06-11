"""
Transform engine — resolve and apply registered transformation rules.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.registry import transform_registry
from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext, TransformMode
from palm.core.transform.exceptions import TransformApplicationError
from palm.core.transform.primitives import register_core_transforms


class TransformEngine(BasePalmEngine):
    """
    Coordinates transformation rules by name.

    Supports single-value transforms, batch list processing, and chained pipelines
    with :class:`TransformContext` preserving original and intermediate views.
    """

    def __init__(self) -> None:
        super().__init__(name="transform")

    def resolve(self, name: str, **options: Any) -> BaseTransform:
        """Instantiate a registered transform rule."""
        cls = transform_registry.get(name)
        build_options = {key: value for key, value in options.items() if not key.startswith("_")}
        return cls.from_options(**build_options)

    def apply(self, name: str, value: Any, **options: Any) -> TransformContext:
        """Apply one rule to ``value`` and return the resulting context."""
        context = TransformContext(original=value)
        transform = self.resolve(name, **options)
        return self._apply_transform(transform, context, **options)

    def apply_chain(
        self,
        names: Sequence[str],
        value: Any,
        *,
        options_by_rule: dict[str, dict[str, Any]] | None = None,
        **shared_options: Any,
    ) -> TransformContext:
        """Apply rules in order, threading the context forward."""
        context = TransformContext(original=value)
        rule_options = options_by_rule or {}
        for name in names:
            merged = {**shared_options, **rule_options.get(name, {})}
            transform = self.resolve(name, **merged)
            context = self._apply_transform(transform, context, **merged)
        return context

    def apply_batch(
        self,
        name: str,
        items: Sequence[Any],
        **options: Any,
    ) -> list[TransformContext]:
        """Apply a rule independently to each item."""
        transform = self.resolve(name, **options)
        results: list[TransformContext] = []
        for item in items:
            context = TransformContext(original=item)
            results.append(self._apply_transform(transform, context, **options))
        return results

    def apply_auto(self, name: str, value: Any, **options: Any) -> TransformContext:
        """
        Apply a rule using its declared mode.

        ``BATCH`` rules receive the whole list; ``SINGLE`` rules receive the scalar;
        ``AUTO`` detects lists and delegates to batch or single accordingly.
        """
        transform = self.resolve(name, **options)
        if transform.mode is TransformMode.BATCH:
            context = TransformContext(original=value)
            return self._apply_transform(transform, context, **options)
        if transform.mode is TransformMode.AUTO and isinstance(value, list):
            context = TransformContext(original=value)
            return self._apply_transform(transform, context, **options)
        return self.apply(name, value, **options)

    def _apply_transform(
        self,
        transform: BaseTransform,
        context: TransformContext,
        **options: Any,
    ) -> TransformContext:
        if not transform.supports(context.value):
            raise TransformApplicationError(
                f"Transform {transform.transform_name!r} does not support "
                f"{type(context.value).__name__}"
            )
        runtime_options = {**options, "_engine": self}
        return transform.apply(context, **runtime_options)

    def _do_initialize(self, **options: Any) -> None:
        register_core_transforms()

    def _do_shutdown(self) -> None:
        pass