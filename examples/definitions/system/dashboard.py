"""System ops dashboard over Palm provider system resources."""

from __future__ import annotations

from palm.definitions.dashboard import DashboardDefinition, DashboardTile
from palm.services.analytics.dashboards import register_dashboard

SYSTEM_OPS_DASHBOARD = DashboardDefinition(
    id="dashboard-palm-system",
    name="palm-system",
    title="Palm System",
    description="Ops tables via provider palm system-read actions",
    tiles=[
        DashboardTile(
            id="waiting",
            dataset="palm-system-waiting",
            profile="table",
            title="Waiting for input",
            limit=50,
        ),
        DashboardTile(
            id="jobs",
            dataset="palm-system-jobs",
            profile="table",
            title="Jobs",
            limit=50,
        ),
        DashboardTile(
            id="instances",
            dataset="palm-system-instances",
            profile="table",
            title="Instances",
            limit=50,
        ),
        DashboardTile(
            id="flows",
            dataset="palm-system-flows",
            profile="table",
            title="Flows",
            limit=100,
        ),
    ],
    metadata={"example": True, "pack": "system"},
)


def register_definitions(repository: object) -> None:
    del repository
    register_dashboard(SYSTEM_OPS_DASHBOARD)


__all__ = ["SYSTEM_OPS_DASHBOARD", "register_definitions"]
