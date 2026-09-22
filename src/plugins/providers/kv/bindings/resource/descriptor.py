"""Provider descriptor for the KV resource provider."""

from __future__ import annotations

from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor


def describe(*, name: str) -> ProviderDescriptor:
    return ProviderDescriptor(
        name=name,
        description="Local key-value storage (memory, durable StorageEngine, or tiered hot/cold)",
        actions=(
            ProviderActionDescriptor(
                "get",
                "Read a value by key; returns {found, value} (missing keys are not failures)",
            ),
            ProviderActionDescriptor(
                "put",
                "Write a value under key (params.value or bound state)",
            ),
            ProviderActionDescriptor(
                "delete",
                "Remove a key",
            ),
            ProviderActionDescriptor(
                "list",
                "List logical keys under optional params.prefix within namespace",
            ),
        ),
    )


__all__ = ["describe"]