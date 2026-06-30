"""Provider descriptor and health for the Palm compositional provider."""

from __future__ import annotations

from palm.core.resource.result import (
    ProviderActionDescriptor,
    ProviderDescriptor,
    ProviderHealth,
)
from palm.providers.palm.bindings.runtimes.wiring import get_bound_runtime


def describe(*, name: str) -> ProviderDescriptor:
    """Return action metadata for catalogs and diagnostics."""
    return ProviderDescriptor(
        name=name,
        description="Compositional Palm orchestration — invoke flows, processes, and resources",
        actions=(
            ProviderActionDescriptor(
                "submit_flow",
                "Submit a child flow by name or flow:<ref>. "
                "Use wait_mode: until_terminal (default when wait=true), "
                "until_input (return when child wizard needs input), "
                "or fire_and_forget.",
            ),
            ProviderActionDescriptor(
                "submit_process",
                "Submit a child process by name or process:<ref>. "
                "Supports the same wait_mode policy as submit_flow.",
            ),
            ProviderActionDescriptor(
                "invoke_resource",
                "Invoke a registered resource definition on the bound runtime",
            ),
            ProviderActionDescriptor(
                "fetch",
                "Fetch job status and result by job id",
            ),
        ),
    )


def health() -> ProviderHealth:
    """Return connectivity signal for local or remote mode."""
    runtime = get_bound_runtime()
    if runtime is not None and runtime.is_started:
        return ProviderHealth(healthy=True, message="local runtime bound")
    return ProviderHealth(
        healthy=False,
        message="no local runtime bound; use remote_url for remote mode",
    )
