"""Filter list items by field equality or truthiness."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_list
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class FilterItemsRule(BaseTransformRule):
    """Filter a list of mappings by field constraint."""

    name: ClassVar[str] = "filter_items"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(
        self,
        *,
        field: str,
        equals: Any | None = None,
        is_truthy: bool = False,
    ) -> None:
        super().__init__()
        self._field = field
        self._equals = equals
        self._is_truthy = is_truthy

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = require_list(context.value, self.rule_name)
        filtered: list[Any] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            if self._is_truthy:
                if item.get(self._field):
                    filtered.append(item)
            elif item.get(self._field) == self._equals:
                filtered.append(item)
        return context.advance(
            self.rule_name,
            filtered,
            meta={
                "field": self._field,
                "equals": self._equals,
                "is_truthy": self._is_truthy,
                "count": len(filtered),
            },
        )
