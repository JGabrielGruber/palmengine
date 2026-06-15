"""Serialize structured data to YAML text (requires PyYAML)."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode


def _yaml_dumper() -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise TransformApplicationError(
            "yaml_dump requires PyYAML — install with: pip install pyyaml",
        ) from exc
    return yaml


class YamlDumpRule(BaseTransformRule):
    """
    Serialize data to a YAML string.

    Options: ``default_flow_style``, ``sort_keys``, ``allow_unicode`` (default ``True``).
    """

    name: ClassVar[str] = "yaml_dump"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> YamlDumpRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        yaml = _yaml_dumper()
        dump_kwargs: dict[str, Any] = {
            "allow_unicode": bool(options.get("allow_unicode", True)),
            "sort_keys": bool(options.get("sort_keys", False)),
        }
        if "default_flow_style" in options:
            dump_kwargs["default_flow_style"] = bool(options["default_flow_style"])
        try:
            result = yaml.dump(context.value, **dump_kwargs)
        except yaml.YAMLError as exc:
            raise TransformApplicationError(
                f"{self.rule_name} value is not YAML serializable: {exc}",
            ) from exc
        if not isinstance(result, str):
            result = str(result)
        return context.advance(self.rule_name, result)
