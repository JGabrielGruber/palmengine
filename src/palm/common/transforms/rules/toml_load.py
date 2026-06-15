"""Parse TOML text into structured data (stdlib ``tomllib``)."""

from __future__ import annotations

import tomllib
from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


class TomlLoadRule(BaseTransformRule):
    """
    Parse TOML text into a mapping.

    Options: ``encoding`` (default ``utf-8`` for bytes input).
    """

    name: ClassVar[str] = "toml_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> TomlLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        encoding = str(options.get("encoding", "utf-8"))
        raw = context.value
        if isinstance(raw, str):
            payload = raw
        elif isinstance(raw, bytes):
            payload = raw.decode(encoding)
        else:
            raise TransformApplicationError(
                f"{self.rule_name} requires str or bytes, got {type(raw).__name__}",
            )
        try:
            parsed = tomllib.loads(payload)
        except tomllib.TOMLDecodeError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} invalid TOML: {exc}",
            ) from exc
        return context.advance(self.rule_name, parsed, meta={"encoding": encoding})