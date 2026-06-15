"""Conditional transforms based on field predicates."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class ConditionalRule(BaseTransformRule):
    """
    Return ``then`` or ``else`` based on predicates over the input.

    For mapping inputs, predicates read ``field``. For scalars, the scalar itself
    is tested when ``field`` is omitted.

    Predicates (first match wins): ``equals``, ``not_equals``, ``gt``, ``gte``,
    ``lt``, ``lte``, ``is_truthy``, ``exists`` (key present when field is set).
    """

    name: ClassVar[str] = "conditional"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> ConditionalRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        if "then" not in options:
            raise TransformApplicationError(f"{self.rule_name} requires then=")
        else_value = options.get("else")

        value = context.value
        field = options.get("field")
        subject: Any
        if field is not None:
            if not isinstance(value, dict):
                raise TransformApplicationError(
                    f"{self.rule_name} field={field!r} requires a mapping input",
                )
            subject = value.get(field)
        else:
            subject = value

        matched = _matches(subject, value if field else None, options)
        result = options["then"] if matched else else_value
        return context.advance(
            self.rule_name,
            result,
            meta={"matched": matched, "field": field},
        )


def _matches(subject: Any, container: dict[str, Any] | None, options: dict[str, Any]) -> bool:
    if "equals" in options:
        return bool(subject == options["equals"])
    if "not_equals" in options:
        return bool(subject != options["not_equals"])
    if "gt" in options:
        return bool(subject > options["gt"])
    if "gte" in options:
        return bool(subject >= options["gte"])
    if "lt" in options:
        return bool(subject < options["lt"])
    if "lte" in options:
        return bool(subject <= options["lte"])
    if options.get("is_truthy"):
        return bool(subject)
    if options.get("exists"):
        if container is None:
            return subject is not None
        field = options.get("field")
        return isinstance(container, dict) and field in container
    raise TransformApplicationError(
        "conditional requires a predicate (equals, gt, gte, is_truthy, exists, ...)",
    )
