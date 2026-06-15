"""Format string values with templates, case transforms, and dates."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode

_CASE_FNS = {
    "upper": str.upper,
    "lower": str.lower,
    "title": str.title,
    "capitalize": str.capitalize,
}


class StringFormatRule(BaseTransformRule):
    """
    Format scalars and mapping fields as strings.

    Options:

    - ``field`` — read this key when the input is a mapping
    - ``template`` — ``str.format`` pattern (``{value}`` for scalars; mapping keys for dicts)
    - ``case`` — ``upper``, ``lower``, ``title``, or ``capitalize``
    - ``date_format`` — ``strftime`` pattern for ``date``/``datetime`` or ISO strings
    """

    name: ClassVar[str] = "string_format"
    mode: ClassVar[TransformMode] = TransformMode.AUTO

    @classmethod
    def from_options(cls, **options: Any) -> StringFormatRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        field = options.get("field")
        if field is not None:
            if not isinstance(value, dict):
                raise TransformApplicationError(
                    f"{self.rule_name} field={field!r} requires a mapping, "
                    f"got {type(value).__name__}",
                )
            value = value.get(field)

        value = self._format_date(value, options.get("date_format"))
        value = self._apply_template(value, context, options.get("template"))
        value = self._apply_case(value, options.get("case"))

        meta = {
            key: options[key]
            for key in ("template", "case", "field", "date_format")
            if options.get(key) is not None
        }
        return context.advance(self.rule_name, value, meta=meta)

    def _format_date(self, value: Any, fmt: str | None) -> Any:
        if not fmt:
            return value
        if isinstance(value, datetime):
            return value.strftime(fmt)
        if isinstance(value, date):
            return value.strftime(fmt)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise TransformApplicationError(
                    f"{self.rule_name} date_format requires a date, datetime, or ISO string",
                ) from exc
            return parsed.strftime(fmt)
        raise TransformApplicationError(
            f"{self.rule_name} date_format requires a date, datetime, or ISO string, "
            f"got {type(value).__name__}",
        )

    def _apply_case(self, value: Any, case: str | None) -> Any:
        if not case or not isinstance(value, str):
            return value
        fn = _CASE_FNS.get(str(case).lower())
        if fn is None:
            raise TransformApplicationError(
                f"{self.rule_name} unknown case {case!r} "
                f"(use upper, lower, title, capitalize)",
            )
        return fn(value)

    def _apply_template(
        self,
        value: Any,
        context: TransformContext,
        template: str | None,
    ) -> Any:
        if not template:
            return value
        try:
            if isinstance(value, dict):
                return template.format(**value)
            if isinstance(context.original, dict):
                return template.format(value=value, **context.original)
            return template.format(value=value)
        except KeyError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} template missing key: {exc.args[0]}",
            ) from exc