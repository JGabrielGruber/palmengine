"""
Transform rule registration helpers for patterns and extensions.

Mirrors :mod:`palm.patterns._registry` — explicit ``register_transform(name, cls)``
at bootstrap time, with an optional decorator for class-based rules.
"""

from __future__ import annotations

from typing import TypeVar

from palm.core.transform.base import BaseTransformRule
from palm.core.transform.registry import transform_registry

T = TypeVar("T", bound=type[BaseTransformRule])


def register_transform(name: str, implementation: type[BaseTransformRule]) -> None:
    """Register a transform rule class under ``name``."""
    transform_registry.register(name, implementation)


def register_transforms(*classes: type[BaseTransformRule]) -> None:
    """Register multiple rule classes using each class's ``name`` ClassVar."""
    for cls in classes:
        register_transform(cls.name, cls)


def transform_rule(cls: T) -> T:
    """Decorator that registers a :class:`BaseTransformRule` using ``cls.name``."""
    register_transform(cls.name, cls)
    return cls


def has_transform(name: str) -> bool:
    """Return whether ``name`` is registered."""
    return name in transform_registry.names()


def registered_transforms() -> list[str]:
    """Return sorted names of registered transform rules."""
    return transform_registry.names()


# Backward-compatible alias for early 0.9.1 callers.
registered_transform_names = registered_transforms
