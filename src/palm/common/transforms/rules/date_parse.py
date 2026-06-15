"""Parse date strings into normalized ISO values."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._dates import parse_datetime_value
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class DateParseRule(BaseTransformRule):
    """
    Parse date/datetime/ISO strings.

    Options:

    - ``input_format`` — optional ``strptime`` pattern for non-ISO strings
    - ``output`` — ``date`` (default, ``YYYY-MM-DD``) or ``datetime`` (ISO datetime)
    """

    name: ClassVar[str] = "date_parse"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> DateParseRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        input_format = options.get("input_format")
        parsed = parse_datetime_value(
            context.value,
            input_format=str(input_format) if input_format else None,
        )
        output = str(options.get("output", "date")).lower()
        if output == "datetime":
            result = parsed.isoformat(timespec="seconds")
        elif output == "date":
            result = parsed.date().isoformat()
        else:
            raise TransformApplicationError(
                f"{self.rule_name} output must be 'date' or 'datetime', got {output!r}",
            )
        return context.advance(
            self.rule_name,
            result,
            meta={"output": output, "input_format": input_format},
        )