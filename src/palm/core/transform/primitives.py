"""
Built-in transform primitives — minimal defaults for wizards and pipelines.

Rich formatting and domain rules belong in ``palm.common.transforms`` later.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, ClassVar

from palm.core.registry import transform_registry
from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext, TransformMode
from palm.core.transform.exceptions import TransformApplicationError


class IdentityTransform(BaseTransform):
    """No-op — useful for testing and explicit chain placeholders."""

    name: ClassVar[str] = "identity"

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        return context.advance(self.transform_name, context.value)


class RenameFieldTransform(BaseTransform):
    """Rename a single key in a mapping."""

    name: ClassVar[str] = "rename_field"

    def __init__(self, *, from_key: str, to_key: str) -> None:
        super().__init__()
        self._from_key = from_key
        self._to_key = to_key

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict):
            raise TransformApplicationError(
                f"{self.transform_name} requires a mapping, got {type(value).__name__}"
            )
        out = dict(value)
        if self._from_key in out:
            out[self._to_key] = out.pop(self._from_key)
        return context.advance(self.transform_name, out, meta={"from": self._from_key, "to": self._to_key})


class PickFieldsTransform(BaseTransform):
    """Keep only selected keys from a mapping."""

    name: ClassVar[str] = "pick_fields"

    def __init__(self, *, fields: list[str]) -> None:
        super().__init__()
        self._fields = list(fields)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict):
            raise TransformApplicationError(
                f"{self.transform_name} requires a mapping, got {type(value).__name__}"
            )
        out = {key: value[key] for key in self._fields if key in value}
        return context.advance(self.transform_name, out, meta={"fields": self._fields})


class FormatValueTransform(BaseTransform):
    """Format a scalar using ``str.format`` or ``strftime`` for dates."""

    name: ClassVar[str] = "format_value"

    def __init__(self, *, template: str = "{value}") -> None:
        super().__init__()
        self._template = template

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if isinstance(value, (datetime, date)):
            fmt = options.get("strftime") or self._template
            try:
                rendered = value.strftime(fmt)
            except (TypeError, ValueError) as exc:
                raise TransformApplicationError(
                    f"{self.transform_name} cannot format date with {fmt!r}"
                ) from exc
        else:
            try:
                rendered = self._template.format(value=value)
            except (KeyError, ValueError, IndexError) as exc:
                raise TransformApplicationError(
                    f"{self.transform_name} cannot format value with template {self._template!r}"
                ) from exc
        return context.advance(self.transform_name, rendered, meta={"template": self._template})


class FilterListTransform(BaseTransform):
    """Filter a list of mappings by a field equality constraint."""

    name: ClassVar[str] = "filter_list"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, field: str, equals: Any) -> None:
        super().__init__()
        self._field = field
        self._equals = equals

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError(
                f"{self.transform_name} requires a list, got {type(value).__name__}"
            )
        filtered = [
            item
            for item in value
            if isinstance(item, dict) and item.get(self._field) == self._equals
        ]
        return context.advance(
            self.transform_name,
            filtered,
            meta={"field": self._field, "equals": self._equals, "count": len(filtered)},
        )


class MapListTransform(BaseTransform):
    """Apply a nested transform rule to each element in a list."""

    name: ClassVar[str] = "map_list"
    mode: ClassVar[TransformMode] = TransformMode.BATCH

    def __init__(self, *, sub_rule: str) -> None:
        super().__init__()
        self._sub_rule = sub_rule

    @classmethod
    def from_options(cls, **options: Any) -> MapListTransform:
        opts = dict(options)
        opts.pop("sub_options", None)
        alias = opts.pop("alias", None)
        instance = cls(sub_rule=str(opts["sub_rule"]))
        if alias is not None:
            instance._alias = alias
        return instance

    def supports(self, value: Any) -> bool:
        return isinstance(value, list)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        from palm.core.transform.engine import TransformEngine

        value = context.value
        if not isinstance(value, list):
            raise TransformApplicationError(
                f"{self.transform_name} requires a list, got {type(value).__name__}"
            )
        engine = options.get("_engine")
        if not isinstance(engine, TransformEngine):
            raise TransformApplicationError(
                f"{self.transform_name} requires TransformEngine injection via options"
            )
        sub_options = dict(options.get("sub_options") or {})
        mapped = [engine.apply(self._sub_rule, item, **sub_options).value for item in value]
        return context.advance(
            self.transform_name,
            mapped,
            meta={"sub_rule": self._sub_rule, "count": len(mapped)},
        )


_CORE_TRANSFORMS: tuple[type[BaseTransform], ...] = (
    IdentityTransform,
    RenameFieldTransform,
    PickFieldsTransform,
    FormatValueTransform,
    FilterListTransform,
    MapListTransform,
)


def register_core_transforms() -> None:
    """Register built-in transforms (idempotent)."""
    for cls in _CORE_TRANSFORMS:
        transform_registry.register(cls.name, cls)