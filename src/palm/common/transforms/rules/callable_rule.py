"""Apply a caller-supplied callable to a value or list of values."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class CallableRule(BaseTransformRule):
    """
    Invoke a Python callable on the current value.

    In ``AUTO`` mode, lists are mapped element-wise; scalars and mappings are
    passed to the callable as a single argument.
    """

    name: ClassVar[str] = "callable"
    mode: ClassVar[TransformMode] = TransformMode.AUTO

    def __init__(self, *, fn: Callable[[Any], Any] | None = None) -> None:
        super().__init__()
        self._fn = fn

    @classmethod
    def from_options(cls, **options: Any) -> CallableRule:
        opts = dict(options)
        alias = opts.pop("alias", None)
        fn = opts.pop("fn", None) or opts.pop("callable", None)
        instance = cls(fn=fn)
        if alias is not None:
            instance._alias = alias
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        fn = options.get("fn") or options.get("callable") or self._fn
        if fn is None or not callable(fn):
            raise TransformApplicationError(
                f"{self.rule_name} requires a callable via fn= or callable=",
            )
        value = context.value
        if isinstance(value, list):
            result = [fn(item) for item in value]
            mode = "per_item"
        else:
            result = fn(value)
            mode = "single"
        return context.advance(self.rule_name, result, meta={"mode": mode})
