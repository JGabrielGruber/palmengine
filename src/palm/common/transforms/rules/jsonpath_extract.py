"""Extract a nested value using a dot-separated path."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._jsonpath import jsonpath_get
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode

_MISSING = object()


class JsonpathExtractRule(BaseTransformRule):
    """Read ``path`` from a mapping or list root."""

    name: ClassVar[str] = "jsonpath_extract"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> JsonpathExtractRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        path = options.get("path")
        if not path:
            raise TransformApplicationError(f"{self.rule_name} requires path=")
        default = options.get("default", _MISSING)
        if default is _MISSING:
            value = jsonpath_get(context.value, str(path))
        else:
            value = jsonpath_get(context.value, str(path), default=default)
        return context.advance(self.rule_name, value, meta={"path": path})
