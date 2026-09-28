"""Provider execution contract — invoke-only verbs (transport-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InvokeOperation = Literal["list", "describe", "invoke"]


@dataclass(frozen=True)
class InvokeVerb:
    """Declarative provider invoke operation."""

    verb_id: str
    operation: InvokeOperation
    summary: str = ""


_registry: list[InvokeVerb] = [
    InvokeVerb("list_providers", "list", "List registered providers"),
    InvokeVerb("describe_provider", "describe", "Describe provider capabilities"),
    InvokeVerb("invoke_provider", "invoke", "Invoke a provider resource"),
]


def invoke_verbs() -> tuple[InvokeVerb, ...]:
    return tuple(_registry)


__all__ = ["InvokeOperation", "InvokeVerb", "invoke_verbs"]