"""Write a nested value using a dot-separated path."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._helpers import require_mapping
from palm.common.transforms.rules._jsonpath import jsonpath_set
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext


class JsonpathSetRule(BaseTransformRule):
    """Return a mapping copy with ``value`` (or ``set_value``) at ``path``."""

    name: ClassVar[str] = "jsonpath_set"

    @classmethod
    def from_options(cls, **options: Any) -> JsonpathSetRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        path = options.get("path")
        if not path:
            raise TransformApplicationError(f"{self.rule_name} requires path=")
        if "set_value" in options:
            set_value = options["set_value"]
        elif "value" in options:
            set_value = options["value"]
        else:
            raise TransformApplicationError(f"{self.rule_name} requires set_value=")
        root = require_mapping(context.value, self.rule_name)
        updated = jsonpath_set(root, str(path), set_value)
        return context.advance(
            self.rule_name,
            updated,
            meta={"path": path, "set_value": set_value},
        )