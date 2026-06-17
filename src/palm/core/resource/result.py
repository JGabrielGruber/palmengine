"""Structured provider invocation results and descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderActionDescriptor:
    """Metadata for a single provider action."""

    name: str
    description: str = ""


@dataclass(frozen=True)
class ProviderDescriptor:
    """Self-description of a provider's capabilities."""

    name: str
    actions: tuple[ProviderActionDescriptor, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class ProviderHealth:
    """Lightweight provider health signal."""

    healthy: bool
    message: str = ""


@dataclass(frozen=True)
class ProviderResult:
    """Outcome of a provider ``invoke`` call."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata: Any) -> ProviderResult:
        """Return a successful result."""
        return cls(success=True, data=data, metadata=dict(metadata))

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> ProviderResult:
        """Return a failed result."""
        return cls(success=False, error=error, metadata=dict(metadata))