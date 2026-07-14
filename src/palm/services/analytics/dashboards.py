"""Dashboard registry + render (0.39) with durable store hook (0.41)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from palm.definitions.dashboard import DashboardDefinition, DashboardTile

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine
    from palm.services.analytics.dashboard_store import DashboardStore
    from palm.services.analytics.service import AnalyticsService

_lock = threading.RLock()
_by_name: dict[str, DashboardDefinition] = {}
_store: DashboardStore | None = None


def attach_dashboard_store(storage: StorageEngine | None) -> int:
    """Bind durable store and load existing dashboards. Return count loaded."""
    global _store
    from palm.services.analytics.dashboard_store import DashboardStore

    with _lock:
        if storage is None:
            _store = None
            return 0
        _store = DashboardStore(storage)
        return _store.load_into_registry()


def register_dashboard(
    dashboard: DashboardDefinition,
    *,
    persist: bool = True,
) -> None:
    with _lock:
        _by_name[dashboard.name] = dashboard
        if persist and _store is not None:
            _store.save(dashboard)


def get_dashboard(name: str) -> DashboardDefinition | None:
    with _lock:
        hit = _by_name.get(str(name or "").strip())
        if hit is not None:
            return hit
        if _store is not None:
            loaded = _store.get(str(name or "").strip())
            if loaded is not None:
                _by_name[loaded.name] = loaded
                return loaded
        return None


def list_dashboards() -> list[dict[str, Any]]:
    with _lock:
        # merge store names not yet in memory
        if _store is not None:
            for name in _store.list_names():
                if name not in _by_name:
                    d = _store.get(name)
                    if d is not None:
                        _by_name[d.name] = d
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
    """Test helper — memory only (does not wipe storage)."""
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


def register_dashboard_from_dict(
    data: dict[str, Any],
    *,
    persist: bool = True,
) -> DashboardDefinition:
    dash = DashboardDefinition.from_dict(data)
    register_dashboard(dash, persist=persist)
    return dash


__all__ = [
    "attach_dashboard_store",
    "clear_dashboards",
    "get_dashboard",
    "list_dashboards",
    "register_dashboard",
    "register_dashboard_from_dict",
    "render_dashboard",
    "DashboardTile",
]
