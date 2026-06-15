"""
Transform contracts — rules, context, and results.

Rules operate on :class:`TransformContext`, which threads the original input,
optional :class:`~palm.core.context.BaseState`, and an audit trail of frames.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from palm.core.context.base_state import BaseState


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
    Immutable views over a transform pipeline.

    ``original`` is preserved for the entire chain. ``value`` is the latest
    result. ``frames`` records every intermediate step for audit and replay.
    An optional ``state`` reference enables scoped reads and writes through
    :class:`~palm.core.transform.engine.TransformEngine`.
    """

    original: Any
    state: BaseState | None = None
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
        return TransformContext(
            original=self.original,
            state=self.state,
            frames=(*self.frames, frame),
        )

    def with_state(self, state: BaseState | None) -> TransformContext:
        """Return a copy bound to ``state``."""
        return TransformContext(
            original=self.original,
            state=state,
            frames=self.frames,
        )

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


@dataclass(frozen=True)
class TransformResult:
    """Outcome of a transform execution."""

    context: TransformContext
    state_writes: tuple[tuple[str, Any], ...] = ()

    @property
    def value(self) -> Any:
        return self.context.value

    @property
    def original(self) -> Any:
        return self.context.original


class BaseTransformRule(ABC):
    """
    Named transformation rule resolved by :class:`~palm.core.transform.engine.TransformEngine`.

    Subclasses declare a registry ``name`` and optional :class:`TransformMode`.
    Configuration is passed via ``from_options`` / ``__init__``; ``apply`` receives
    the current :class:`TransformContext` and returns an advanced context.
    """

    name: ClassVar[str] = "base"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    def __init__(self, *, alias: str | None = None) -> None:
        self._alias = alias

    @property
    def rule_name(self) -> str:
        return self._alias or self.name

    @classmethod
    def from_options(cls, **options: Any) -> BaseTransformRule:
        """Build a rule instance from engine options."""
        opts = dict(options)
        alias = opts.pop("alias", None)
        instance = cls(**opts)
        if alias is not None:
            instance._alias = alias
        return instance

    @abstractmethod
    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        """Transform ``context.value`` and return the advanced context."""

    def supports(self, value: Any) -> bool:
        """Return whether this rule can process ``value`` (override for strict rules)."""
        return True
