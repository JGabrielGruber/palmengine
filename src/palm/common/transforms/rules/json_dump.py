"""Serialize structured data to a JSON string."""

from __future__ import annotations

import json
from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class JsonDumpRule(BaseTransformRule):
    """
    Serialize a mapping or list to a JSON string.

    Options: ``indent``, ``ensure_ascii`` (default ``False``), ``sort_keys``,
    ``separators`` (two-tuple), ``default`` (non-JSON-serializable fallback).
    """

    name: ClassVar[str] = "json_dump"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> JsonDumpRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        value = context.value
        if not isinstance(value, dict | list):
            raise TransformApplicationError(
                f"{self.rule_name} requires a mapping or list, got {type(value).__name__}",
            )
        indent = options.get("indent")
        ensure_ascii = bool(options.get("ensure_ascii", False))
        sort_keys = bool(options.get("sort_keys", False))
        separators = options.get("separators")
        default = options.get("default")
        dump_kwargs: dict[str, Any] = {
            "ensure_ascii": ensure_ascii,
            "sort_keys": sort_keys,
        }
        if indent is not None:
            dump_kwargs["indent"] = indent
        if isinstance(separators, list | tuple) and len(separators) == 2:
            dump_kwargs["separators"] = tuple(separators)
        if default is not None:
            dump_kwargs["default"] = default
        try:
            result = json.dumps(value, **dump_kwargs)
        except TypeError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} value is not JSON serializable: {exc}",
            ) from exc
        return context.advance(self.rule_name, result, meta={"ensure_ascii": ensure_ascii})
