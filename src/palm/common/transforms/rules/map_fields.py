"""Map multiple source keys to target keys in a mapping."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_mapping
from palm.core.transform.base import BaseTransformRule, TransformContext


class MapFieldsRule(BaseTransformRule):
    """Apply a key mapping to a dict-valued payload."""

    name: ClassVar[str] = "map_fields"

    def __init__(self, *, mapping: Mapping[str, str], keep_unmapped: bool = True) -> None:
        super().__init__()
        self._mapping = dict(mapping)
        self._keep_unmapped = keep_unmapped

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = require_mapping(context.value, self.rule_name)
        if self._keep_unmapped:
            out = dict(value)
            for from_key, to_key in self._mapping.items():
                if from_key in out:
                    out[to_key] = out.pop(from_key)
        else:
            out = {
                to_key: value[from_key]
                for from_key, to_key in self._mapping.items()
                if from_key in value
            }
        return context.advance(
            self.rule_name,
            out,
            meta={"mapping": self._mapping, "keep_unmapped": self._keep_unmapped},
        )
