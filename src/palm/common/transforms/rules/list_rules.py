"""List transforms — filter and map with rich conditions."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext, TransformMode
from palm.core.transform.engine import TransformEngine
from palm.core.transform.exceptions import TransformApplicationError


class FilterListTransform(BaseTransform):
    """
    Filter a list of mappings by field conditions.

    Supports ``equals``, ``not_equals``, ``contains``, ``in``, and ``truthy``.
    """

    name: ClassVar[str] = "filter_list"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(
        self,
        *,
        field: str | None = None,
        equals: Any = None,
        not_equals: Any = None,
        contains: str | None = None,
        in_values: list[Any] | None = None,
        truthy: bool | None = None,
    ) -> None:
        super().__init__()
        self._field = field
        self._equals = equals
        self._not_equals = not_equals
        self._contains = contains
        self._in_values = list(in_values) if in_values is not None else None
        self._truthy = truthy

    @classmethod
    def from_options(cls, **options: Any) -> FilterListTransform:
        in_raw = options.get("in") or options.get("in_values")
        return cls(
            field=options.get("field"),
            equals=options.get("equals"),
            not_equals=options.get("not_equals"),
            contains=options.get("contains"),
            in_values=list(in_raw) if isinstance(in_raw, list) else None,
            truthy=options.get("truthy"),
        )

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError(
                f"{self.transform_name} requires a list, got {type(value).__name__}"
            )
        filtered = [item for item in value if self._matches(item)]
        return context.advance(
            self.transform_name,
            filtered,
            meta={"field": self._field, "count": len(filtered)},
        )

    def _matches(self, item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        candidate = item.get(self._field) if self._field else item
        if self._equals is not None and candidate != self._equals:
            return False
        if self._not_equals is not None and candidate == self._not_equals:
            return False
        if self._contains is not None:
            text = str(candidate)
            if self._contains not in text:
                return False
        if self._in_values is not None and candidate not in self._in_values:
            return False
        if self._truthy is not None and bool(candidate) != self._truthy:
            return False
        return True


class MapListTransform(BaseTransform):
    """Apply a nested transform rule to each list element."""

    name: ClassVar[str] = "map_list"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, sub_rule: str) -> None:
        super().__init__()
        self._sub_rule = sub_rule

    @classmethod
    def from_options(cls, **options: Any) -> MapListTransform:
        opts = dict(options)
        opts.pop("sub_options", None)
        return cls(sub_rule=str(opts["sub_rule"]))

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError(
                f"{self.transform_name} requires a list, got {type(value).__name__}"
            )
        engine = options.get("_engine")
        if not isinstance(engine, TransformEngine):
            raise TransformApplicationError(
                f"{self.transform_name} requires TransformEngine injection"
            )
        sub_options = dict(options.get("sub_options") or {})
        mapped = [engine.apply(self._sub_rule, item, **sub_options).value for item in value]
        return context.advance(
            self.transform_name,
            mapped,
            meta={"sub_rule": self._sub_rule, "count": len(mapped)},
        )