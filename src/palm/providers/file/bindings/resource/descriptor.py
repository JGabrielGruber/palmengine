"""Provider descriptor for the file document resource provider."""

from __future__ import annotations

from palm.core.resource.result import ProviderActionDescriptor, ProviderDescriptor


def describe(*, name: str) -> ProviderDescriptor:
    return ProviderDescriptor(
        name=name,
        description="Local filesystem documents under host data_dir/documents",
        actions=(
            ProviderActionDescriptor(
                "read",
                "Read a document by relative path; returns {content, path}",
            ),
            ProviderActionDescriptor(
                "write",
                "Write params.content or params.value to a relative document path",
            ),
            ProviderActionDescriptor(
                "delete",
                "Delete a document by relative path",
            ),
            ProviderActionDescriptor(
                "exists",
                "Check whether a document path exists",
            ),
            ProviderActionDescriptor(
                "list",
                "List document paths under optional params.glob",
            ),
        ),
    )


__all__ = ["describe"]