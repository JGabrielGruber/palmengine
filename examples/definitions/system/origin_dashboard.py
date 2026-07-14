"""Dashboard tiles bound to **origin-*** datasets (definition-fixed remote)."""

from __future__ import annotations

from palm.definitions.dashboard import DashboardDefinition, DashboardTile
from palm.services.analytics.dashboards import register_dashboard

_DEFAULT_PREFIX = "origin"


def make_origin_system_dashboard(
    *,
    name_prefix: str = _DEFAULT_PREFIX,
    remote_url: str | None = None,
) -> DashboardDefinition:
    prefix = (name_prefix or _DEFAULT_PREFIX).strip().rstrip("-") or _DEFAULT_PREFIX
    title_suffix = f" @ {remote_url}" if remote_url else ""
    return DashboardDefinition(
        id=f"dashboard-{prefix}-system",
        name=f"{prefix}-system",
        title=f"Origin Palm System{title_suffix}",
        description=(
            "Ops tables for a remote Palm — each tile uses a ResourceDefinition "
            "with params.remote_url (not query-time params)"
        ),
        tiles=[
            DashboardTile(
                id="waiting",
                dataset=f"{prefix}-system-waiting",
                profile="table",
                title="Waiting (origin)",
                limit=50,
            ),
            DashboardTile(
                id="jobs",
                dataset=f"{prefix}-system-jobs",
                profile="table",
                title="Jobs (origin)",
                limit=50,
            ),
            DashboardTile(
                id="instances",
                dataset=f"{prefix}-system-instances",
                profile="table",
                title="Instances (origin)",
                limit=50,
            ),
            DashboardTile(
                id="instances_per_flow",
                dataset=f"{prefix}-system-instances-per-flow",
                profile="series",
                title="Instances per flow (origin)",
                series={"x_field": "flow_name", "y_fields": ["count"]},
                limit=50,
            ),
            DashboardTile(
                id="flows",
                dataset=f"{prefix}-system-flows",
                profile="table",
                title="Flows (origin)",
                limit=100,
            ),
        ],
        metadata={
            "example": True,
            "pack": "system",
            "origin": True,
            "name_prefix": prefix,
        },
    )


def register_origin_system_dashboard(
    *,
    name_prefix: str = _DEFAULT_PREFIX,
    remote_url: str | None = None,
) -> DashboardDefinition:
    dash = make_origin_system_dashboard(
        name_prefix=name_prefix,
        remote_url=remote_url,
    )
    register_dashboard(dash)
    return dash


__all__ = [
    "make_origin_system_dashboard",
    "register_origin_system_dashboard",
]
