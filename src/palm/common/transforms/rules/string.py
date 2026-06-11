"""String and date formatting transforms."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, ClassVar

from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext
from palm.core.transform.exceptions import TransformApplicationError


class UppercaseTransform(BaseTransform):
    name: ClassVar[str] = "uppercase"

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, str):
            raise TransformApplicationError(
                f"{self.transform_name} requires str, got {type(value).__name__}"
            )
        return context.advance(self.transform_name, value.upper())


class LowercaseTransform(BaseTransform):
    name: ClassVar[str] = "lowercase"

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, str):
            raise TransformApplicationError(
                f"{self.transform_name} requires str, got {type(value).__name__}"
            )
        return context.advance(self.transform_name, value.lower())


class FormatStringTransform(BaseTransform):
    name: ClassVar[str] = "format_string"

    def __init__(self, *, template: str = "{value}") -> None:
        super().__init__()
        self._template = template

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        try:
            rendered = self._template.format(value=value, **options)
        except (KeyError, ValueError, IndexError) as exc:
            raise TransformApplicationError(
                f"{self.transform_name} failed with template {self._template!r}"
            ) from exc
        return context.advance(self.transform_name, rendered, meta={"template": self._template})


class FormatDateTransform(BaseTransform):
    name: ClassVar[str] = "format_date"

    def __init__(self, *, fmt: str = "%Y-%m-%d") -> None:
        super().__init__()
        self._fmt = fmt

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        parsed = _coerce_date(value)
        try:
            rendered = parsed.strftime(options.get("fmt") or self._fmt)
        except (TypeError, ValueError) as exc:
            raise TransformApplicationError(f"{self.transform_name} cannot format date") from exc
        return context.advance(self.transform_name, rendered, meta={"fmt": self._fmt})


def _coerce_date(value: Any) -> date | datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise TransformApplicationError(f"Cannot parse date string: {value!r}") from exc
    raise TransformApplicationError(f"format_date requires date/datetime/str, got {type(value).__name__}")