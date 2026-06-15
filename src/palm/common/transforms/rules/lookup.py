"""Map keys through a static lookup table."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode

_MISSING = object()


class LookupRule(BaseTransformRule):
    """
    Resolve a key via ``table`` (or ``mapping``).

    For mapping inputs, read ``key_field`` (default ``key``). Scalars are used
    directly as lookup keys. Unknown keys return ``default`` when provided.
    """

    name: ClassVar[str] = "lookup"
    mode: ClassVar[TransformMode] = TransformMode.AUTO

    @classmethod
    def from_options(cls, **options: Any) -> LookupRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        table = options.get("table") or options.get("mapping")
        if not isinstance(table, dict):
            raise TransformApplicationError(f"{self.rule_name} requires table=")

        value = context.value
        key_field = options.get("key_field", "key")
        if isinstance(value, dict):
            lookup_key = value.get(key_field, value.get("id"))
        else:
            lookup_key = value

        if lookup_key is None:
            raise TransformApplicationError(
                f"{self.rule_name} could not determine lookup key from input",
            )

        if lookup_key in table:
            result = table[lookup_key]
        elif "default" in options:
            result = options["default"]
        else:
            raise TransformApplicationError(
                f"{self.rule_name} no entry for key {lookup_key!r}",
            )

        return context.advance(
            self.rule_name,
            result,
            meta={"key": lookup_key, "hit": lookup_key in table},
        )