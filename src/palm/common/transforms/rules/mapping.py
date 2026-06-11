"""Mapping transforms — rename, pick, and drop fields."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext
from palm.core.transform.exceptions import TransformApplicationError


def _require_mapping(value: Any, rule: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TransformApplicationError(f"{rule} requires a mapping, got {type(value).__name__}")
    return dict(value)


class RenameTransform(BaseTransform):
    """Rename a key in a mapping (alias: ``rename``)."""

    name: ClassVar[str] = "rename"

    def __init__(self, *, from_key: str, to_key: str) -> None:
        super().__init__()
        self._from_key = from_key
        self._to_key = to_key

    @classmethod
    def from_options(cls, **options: Any) -> RenameTransform:
        from_key = options.get("from_key") or options.get("from")
        to_key = options.get("to_key") or options.get("to")
        if not from_key or not to_key:
            raise TransformApplicationError("rename requires from_key/to_key (or from/to)")
        return cls(from_key=str(from_key), to_key=str(to_key))

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        out = _require_mapping(context.value, self.transform_name)
        if self._from_key in out:
            out[self._to_key] = out.pop(self._from_key)
        return context.advance(self.transform_name, out)


class PickFieldsTransform(BaseTransform):
    """Keep only selected keys (alias: ``pick_fields``)."""

    name: ClassVar[str] = "pick_fields"

    def __init__(self, *, fields: list[str]) -> None:
        super().__init__()
        self._fields = list(fields)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = _require_mapping(context.value, self.transform_name)
        out = {key: value[key] for key in self._fields if key in value}
        return context.advance(self.transform_name, out, meta={"fields": self._fields})


class DropFieldsTransform(BaseTransform):
    """Remove keys from a mapping."""

    name: ClassVar[str] = "drop_fields"

    def __init__(self, *, fields: list[str]) -> None:
        super().__init__()
        self._fields = list(fields)

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = _require_mapping(context.value, self.transform_name)
        out = {key: val for key, val in value.items() if key not in self._fields}
        return context.advance(self.transform_name, out, meta={"dropped": self._fields})