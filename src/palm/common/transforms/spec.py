"""
Declarative transform specifications — rules, options, and pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TransformSpec:
    """Single transform rule invocation."""

    rule: str
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> TransformSpec:
        if "rule" not in data:
            raise ValueError("Transform spec requires 'rule'")
        options = {key: value for key, value in data.items() if key != "rule"}
        return cls(rule=str(data["rule"]), options=options)


@dataclass(frozen=True)
class TransformPipeline:
    """Ordered chain of transform rules."""

    steps: tuple[TransformSpec, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("TransformPipeline requires at least one step")

    @classmethod
    def parse(cls, raw: Any) -> TransformPipeline | None:
        """
        Parse declarative transform config from flow definitions.

        Supported shapes::

            {"rule": "pick_fields", "fields": ["id", "label"]}
            {"chain": [{"rule": "filter_list", ...}, {"rule": "map_list", ...}]}
            [{"rule": "rename", "from_key": "a", "to_key": "b"}]
        """
        if raw is None:
            return None
        if isinstance(raw, TransformPipeline):
            return raw
        if isinstance(raw, TransformSpec):
            return cls(steps=(raw,))
        if isinstance(raw, dict):
            if "chain" in raw:
                chain = raw["chain"]
                if not isinstance(chain, list):
                    raise ValueError("transform.chain must be a list")
                return cls(steps=tuple(TransformSpec.from_mapping(item) for item in chain))
            return cls(steps=(TransformSpec.from_mapping(raw),))
        if isinstance(raw, list):
            return cls(steps=tuple(TransformSpec.from_mapping(item) for item in raw))
        raise ValueError(f"Unsupported transform config: {type(raw).__name__}")

    @property
    def rule_names(self) -> tuple[str, ...]:
        return tuple(step.rule for step in self.steps)