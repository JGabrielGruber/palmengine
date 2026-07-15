"""Durable dashboard definitions on StorageEngine (0.41)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.definitions.dashboard import DashboardDefinition

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine

DASHBOARD_INDEX = "palm:dashboard:index"
DASHBOARD_PREFIX = "palm:dashboard:def:"


class DashboardStore:
    """Persist :class:`DashboardDefinition` by name."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def save(self, dashboard: DashboardDefinition) -> None:
        name = str(dashboard.name or "").strip()
        if not name:
            raise ValueError("dashboard name required")
        self._storage.set(f"{DASHBOARD_PREFIX}{name}", dashboard.to_dict())
        index = self._load_index()
        if name not in index:
            index.append(name)
            index.sort()
            self._storage.set(DASHBOARD_INDEX, index)

    def get(self, name: str) -> DashboardDefinition | None:
        key = str(name or "").strip()
        raw = self._storage.get(f"{DASHBOARD_PREFIX}{key}")
        if not isinstance(raw, dict):
            return None
        return DashboardDefinition.from_dict(raw)

    def list_names(self) -> list[str]:
        return list(self._load_index())

    def list_all(self) -> list[DashboardDefinition]:
        out: list[DashboardDefinition] = []
        for name in self.list_names():
            d = self.get(name)
            if d is not None:
                out.append(d)
        return out

    def delete(self, name: str) -> bool:
        key = str(name or "").strip()
        had = self._storage.get(f"{DASHBOARD_PREFIX}{key}") is not None
        self._storage.delete(f"{DASHBOARD_PREFIX}{key}")
        index = [n for n in self._load_index() if n != key]
        self._storage.set(DASHBOARD_INDEX, index)
        return had

    def load_into_registry(self) -> int:
        """Hydrate in-process registry from storage; return count loaded."""
        from palm.services.analytics.dashboards import register_dashboard

        n = 0
        for d in self.list_all():
            register_dashboard(d, persist=False)
            n += 1
        return n

    def _load_index(self) -> list[str]:
        raw = self._storage.get(DASHBOARD_INDEX)
        if isinstance(raw, list):
            return [str(x) for x in raw if x]
        return []


__all__ = ["DASHBOARD_INDEX", "DASHBOARD_PREFIX", "DashboardStore"]
