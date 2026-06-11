"""
Abstract transform rule contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from palm.core.transform.context import TransformContext, TransformMode


class BaseTransform(ABC):
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
    def transform_name(self) -> str:
        return self._alias or self.name

    @classmethod
    def from_options(cls, **options: Any) -> BaseTransform:
        """Build a rule instance from engine/leaf options."""
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