"""Pipeline pattern configuration — ordered transform steps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.transforms.builder import TransformStepSpec, transform_step_from_mapping


@dataclass(frozen=True)
class PipelineConfig:
    """Declarative pipeline of transform steps."""

    steps: tuple[TransformStepSpec, ...]
    initial_state: dict[str, Any] | None = None

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> PipelineConfig:
        """Parse pipeline options from a flow definition."""
        steps_raw = options.get("steps")
        if not isinstance(steps_raw, list) or not steps_raw:
            raise ValueError("Pipeline requires a non-empty 'steps' list")

        steps = tuple(
            transform_step_from_mapping(item) for item in steps_raw if isinstance(item, dict)
        )
        if not steps:
            raise ValueError("Pipeline 'steps' must contain step dicts")

        initial = options.get("initial_state")
        initial_state = dict(initial) if isinstance(initial, dict) else None
        return cls(steps=steps, initial_state=initial_state)
