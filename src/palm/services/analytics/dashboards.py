"""In-process dashboard registry + render (0.39)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from palm.definitions.dashboard import DashboardDefinition, DashboardTile

if TYPE_CHECKING:
    from palm.services.analytics.service import AnalyticsService

_lock = threading.RLock()
_by_name: dict[str, DashboardDefinition] = {}


def register_dashboard(dashboard: DashboardDefinition) -> None:
    with _lock:
        _by_name[dashboard.name] = dashboard


def get_dashboard(name: str) -> DashboardDefinition | None:
    with _lock:
        return _by_name.get(str(name or "").strip())


def list_dashboards() -> list[dict[str, Any]]:
    with _lock:
        return [
            {
                "name": d.name,
                "id": d.definition_id,
                "title": d.title or d.name,
                "description": d.description,
                "tile_count": len(d.tiles),
            }
            for d in sorted(_by_name.values(), key=lambda x: x.name)
        ]


def clear_dashboards() -> None:
    """Test helper."""
    with _lock:
        _by_name.clear()


def render_dashboard(
    analytics: AnalyticsService,
    name: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load dashboard definition and query each tile (no joins)."""
    dash = get_dashboard(name)
    if dash is None:
        return {
            "status": "error",
            "dashboard": name,
            "error": f"Dashboard not found: {name}",
            "code": "dashboard_not_found",
        }
    tiles_out: list[dict[str, Any]] = []
    for tile in dash.tiles:
        q = analytics.query(
            tile.dataset,
            profile=tile.profile,
            params=params,
            select=tile.select,
            limit=tile.limit,
            series=tile.series,
            kpi=tile.kpi,
        )
        tiles_out.append(
            {
                "tile": tile.to_dict(),
                "result": q,
            }
        )
    return {
        "status": "ok",
        "dashboard": dash.to_dict(),
        "tiles": tiles_out,
    }


def register_dashboard_from_dict(data: dict[str, Any]) -> DashboardDefinition:
    dash = DashboardDefinition.from_dict(data)
    register_dashboard(dash)
    return dash


__all__ = [
    "clear_dashboards",
    "get_dashboard",
    "list_dashboards",
    "register_dashboard",
    "register_dashboard_from_dict",
    "render_dashboard",
]
