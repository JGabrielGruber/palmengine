"""Palm todos analytics dashboard (0.39) — definition tiles only."""

from __future__ import annotations

from palm.definitions.dashboard import DashboardDefinition, DashboardTile
from palm.services.analytics.dashboards import register_dashboard

TODOS_DASHBOARD = DashboardDefinition(
    id="dashboard-palm-todos",
    name="palm-todos",
    title="Palm Todos",
    description="Fact table + virtual priority series from todo-builder",
    tiles=[
        DashboardTile(
            id="list",
            dataset="palm-todos",
            profile="table",
            title="All todos",
            select=["title", "priority", "due_date"],
            limit=50,
        ),
        DashboardTile(
            id="by_priority",
            dataset="palm-todos-by-priority",
            profile="series",
            title="By priority",
            series={"x_field": "priority", "y_fields": ["count"]},
            limit=20,
        ),
        DashboardTile(
            id="count_kpi",
            dataset="palm-todos-by-priority",
            profile="kpi",
            title="Total items",
            kpi={"field": "count", "agg": "sum", "label": "Todos"},
        ),
    ],
    metadata={"example": True, "pack": "todos"},
)


def register_definitions(repository: object) -> None:
    """Register dashboard (in-process registry; repository unused)."""
    del repository  # pack resources/flows use repository; dashboards are live registry
    register_dashboard(TODOS_DASHBOARD)


__all__ = ["TODOS_DASHBOARD", "register_definitions"]
