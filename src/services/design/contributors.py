"""Drain design contributor hooks into the design service registry."""

from __future__ import annotations

from palm.common.patterns._registry import DesignContributorHook
from palm.common.providers._registry import DesignContributorHookFn
from palm.core.registry import Registry


def wire_builtin_design_contributors(
    *,
    pattern_hooks: Registry[DesignContributorHook],
    provider_hooks: Registry[DesignContributorHookFn],
) -> None:
    """Drain the design hooks the caller passes.

    A name that is not installed is not read from the process hook maps.
    """
    for name in pattern_hooks.names():
        pattern_hooks.get(name).register()
    for name in provider_hooks.names():
        provider_hooks.get(name)()
    # 0.41.2 — dashboard tile validation
    from services.analytics.dashboard_design import (
        validate_dashboard_design_proposal,
    )
    from services.design.registry import (
        DesignContributor,
        register_design_contributor,
    )

    register_design_contributor(
        DesignContributor(
            contributor_id="dashboard",
            validate=validate_dashboard_design_proposal,
            summary="Dashboard tile structure and profile validation (0.41)",
        ),
    )


__all__ = ["wire_builtin_design_contributors"]
