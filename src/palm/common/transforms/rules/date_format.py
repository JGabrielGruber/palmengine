"""Format date-like values with strftime patterns."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._dates import format_datetime_value
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class DateFormatRule(BaseTransformRule):
    """Format ``date``/``datetime``/ISO strings using ``format`` (strftime pattern)."""

    name: ClassVar[str] = "date_format"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> DateFormatRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        fmt = options.get("format")
        if not fmt:
            raise TransformApplicationError(f"{self.rule_name} requires format=")
        input_format = options.get("input_format")
        result = format_datetime_value(
            context.value,
            str(fmt),
            input_format=str(input_format) if input_format else None,
        )
        return context.advance(self.rule_name, result, meta={"format": fmt})
