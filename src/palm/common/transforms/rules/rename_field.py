"""Rename a single key in a mapping."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_mapping
from palm.core.transform.base import BaseTransformRule, TransformContext


class RenameFieldRule(BaseTransformRule):
    """Rename one key in a dict-valued payload."""

    name: ClassVar[str] = "rename_field"

    def __init__(self, *, from_key: str, to_key: str) -> None:
        super().__init__()
        self._from_key = from_key
        self._to_key = to_key

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = require_mapping(context.value, self.rule_name)
        out = dict(value)
        if self._from_key in out:
            out[self._to_key] = out.pop(self._from_key)
        return context.advance(
            self.rule_name,
            out,
            meta={"from": self._from_key, "to": self._to_key},
        )
