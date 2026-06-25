"""Provider descriptor for the REST resource provider."""

from __future__ import annotations

from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor


def describe(*, name: str) -> ProviderDescriptor:
    return ProviderDescriptor(
        name=name,
        description="HTTP REST resource access",
        actions=(
            ProviderActionDescriptor(
                "fetch",
                "GET a resource by path or id (requires base_url param or absolute URL)",
            ),
        ),
    )