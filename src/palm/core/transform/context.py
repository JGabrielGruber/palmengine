"""
Transform context — immutable pipeline state with original + intermediate views.

Each applied rule appends a :class:`TransformFrame`. Callers can read the
current value, the original input, or lens into any named step in the chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TransformMode(StrEnum):
    """How a transform rule expects to process values."""

    SINGLE = "single"
    BATCH = "batch"
    AUTO = "auto"


@dataclass(frozen=True)
class TransformFrame:
    """One step in a transform chain."""

    rule: str
    value: Any
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransformContext:
    """
    Immutable views/lenses over a transform pipeline.

    ``original`` is preserved for the entire chain. ``value`` is the latest
    result. ``frames`` records every intermediate step for audit and replay.
    """

    original: Any
    frames: tuple[TransformFrame, ...] = ()

    @property
    def value(self) -> Any:
        if self.frames:
            return self.frames[-1].value
        return self.original

    @property
    def steps(self) -> tuple[str, ...]:
        return tuple(frame.rule for frame in self.frames)

    def advance(
        self,
        rule: str,
        value: Any,
        *,
        meta: dict[str, Any] | None = None,
    ) -> TransformContext:
        """Return a new context with ``value`` recorded under ``rule``."""
        frame = TransformFrame(rule=rule, value=value, meta=dict(meta or {}))
        return TransformContext(original=self.original, frames=(*self.frames, frame))

    def lens(self, rule: str) -> Any | None:
        """Return the value produced by the most recent frame named ``rule``."""
        for frame in reversed(self.frames):
            if frame.rule == rule:
                return frame.value
        return None

    def to_trace(self) -> dict[str, Any]:
        """Serialize the pipeline for blackboard audit keys."""
        return {
            "original": self.original,
            "value": self.value,
            "steps": list(self.steps),
            "frames": [
                {"rule": frame.rule, "value": frame.value, "meta": dict(frame.meta)}
                for frame in self.frames
            ],
        }