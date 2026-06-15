"""Evaluate safe arithmetic expressions against variables."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._math import evaluate_expression
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext


class CalculateRule(BaseTransformRule):
    """
    Evaluate ``expression`` with variables from the payload and ``variables`` option.

    When the input is a mapping, its keys become variables. Use ``variables`` to
    add or override names. Example: ``expression="price * qty"``.
    """

    name: ClassVar[str] = "calculate"

    @classmethod
    def from_options(cls, **options: Any) -> CalculateRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        expression = options.get("expression")
        if not expression:
            raise TransformApplicationError(f"{self.rule_name} requires expression=")
        variables: dict[str, Any] = {}
        if isinstance(context.value, dict):
            variables.update(context.value)
        extra = options.get("variables")
        if isinstance(extra, dict):
            variables.update(extra)
        if not variables:
            raise TransformApplicationError(
                f"{self.rule_name} requires variables from a mapping or variables=",
            )
        result = evaluate_expression(str(expression), variables)
        return context.advance(
            self.rule_name,
            result,
            meta={"expression": expression, "variables": sorted(variables)},
        )