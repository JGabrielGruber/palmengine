"""Count list items by a field value — definition-only rollups (e.g. analytics views)."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_list
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class CountByRule(BaseTransformRule):
    """
    Group a list of mappings by ``field`` and emit ``[{field, count}, ...]``.

    Example (wizard/pipeline transform step)::

        rule: count_by
        source_key: todos
        target_key: by_priority
        options: {field: priority}
    """

    name: ClassVar[str] = "count_by"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, field: str, count_key: str = "count") -> None:
        super().__init__()
        self._field = field
        self._count_key = count_key

    @classmethod
    def from_options(cls, **options: Any) -> CountByRule:
        field = options.get("field")
        if not field:
            raise TransformApplicationError("count_by requires field=")
        count_key = str(options.get("count_key") or "count")
        return cls(field=str(field), count_key=count_key)

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        field = str(options.get("field") or self._field)
        count_key = str(options.get("count_key") or self._count_key)
        if not field:
            raise TransformApplicationError(f"{self.rule_name} requires field=")
        value = require_list(context.value, self.rule_name)
        counts: dict[str, int] = {}
        order: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            key = item.get(field)
            label = "unknown" if key is None or key == "" else str(key)
            if label not in counts:
                order.append(label)
                counts[label] = 0
            counts[label] += 1
        rows = [{field: k, count_key: counts[k]} for k in order]
        return context.advance(
            self.rule_name,
            rows,
            meta={"field": field, "groups": len(rows), "count_key": count_key},
        )
