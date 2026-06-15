"""Parse JSON text into structured data."""

from __future__ import annotations

import json
from typing import Any, ClassVar

from palm.common.transforms.rules._formats import ensure_text
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class JsonLoadRule(BaseTransformRule):
    """
    Parse a JSON string or bytes into dict/list.

    Options: ``encoding`` (default ``utf-8`` for bytes), ``strict`` (default ``True``).
    """

    name: ClassVar[str] = "json_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> JsonLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        encoding = str(options.get("encoding", "utf-8"))
        strict = bool(options.get("strict", True))
        text = ensure_text(context.value, encoding=encoding, rule_name=self.rule_name)
        try:
            parsed = json.loads(text, strict=strict)
        except json.JSONDecodeError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} invalid JSON at line {exc.lineno} col {exc.colno}: {exc.msg}",
            ) from exc
        return context.advance(self.rule_name, parsed, meta={"encoding": encoding})
