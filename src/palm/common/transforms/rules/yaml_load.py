"""Parse YAML text into structured data (requires PyYAML)."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.rules._formats import ensure_text
from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


def _yaml_loader(*, safe: bool) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise TransformApplicationError(
            "yaml_load requires PyYAML — install with: pip install pyyaml",
        ) from exc
    return yaml.safe_load if safe else yaml.load


class YamlLoadRule(BaseTransformRule):
    """
    Parse YAML text into Python data.

    Options: ``encoding`` (default ``utf-8``), ``safe`` (default ``True``, uses
    ``yaml.safe_load``).
    """

    name: ClassVar[str] = "yaml_load"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> YamlLoadRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        encoding = str(options.get("encoding", "utf-8"))
        safe = bool(options.get("safe", True))
        text = ensure_text(context.value, encoding=encoding, rule_name=self.rule_name)
        loader = _yaml_loader(safe=safe)
        try:
            parsed = loader(text)
        except Exception as exc:
            raise TransformApplicationError(
                f"{self.rule_name} invalid YAML: {exc}",
            ) from exc
        return context.advance(self.rule_name, parsed, meta={"safe": safe})
