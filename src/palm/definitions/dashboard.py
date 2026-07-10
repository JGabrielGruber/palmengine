"""
Dashboard definition — layout of analytics tiles (0.39).

Pure contract data. No query logic; AnalyticsService renders tiles via query().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_DEFINITION_VERSION = 1


@dataclass
class DashboardTile:
    """One bound chart/table on a dashboard."""

    id: str
    dataset: str
    profile: str = "table"  # raw | table | series | kpi
    title: str = ""
    options: dict[str, Any] = field(default_factory=dict)
    # profile-specific: select, limit, series, kpi
    select: list[str] | None = None
    limit: int | None = None
    series: dict[str, Any] | None = None
    kpi: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DashboardTile id must be non-empty")
        if not self.dataset:
            raise ValueError("DashboardTile dataset must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "dataset": self.dataset,
            "profile": self.profile,
            "title": self.title or self.dataset,
            "options": dict(self.options),
        }
        if self.select is not None:
            out["select"] = list(self.select)
        if self.limit is not None:
            out["limit"] = self.limit
        if self.series is not None:
            out["series"] = dict(self.series)
        if self.kpi is not None:
            out["kpi"] = dict(self.kpi)
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardTile:
        return cls(
            id=str(data.get("id") or data.get("tile_id") or ""),
            dataset=str(data.get("dataset") or ""),
            profile=str(data.get("profile") or "table"),
            title=str(data.get("title") or ""),
            options=dict(data.get("options") or {}),
            select=list(data["select"]) if isinstance(data.get("select"), list) else None,
            limit=int(data["limit"]) if data.get("limit") is not None else None,
            series=dict(data["series"]) if isinstance(data.get("series"), dict) else None,
            kpi=dict(data["kpi"]) if isinstance(data.get("kpi"), dict) else None,
        )


@dataclass
class DashboardDefinition:
    """Named dashboard: ordered tiles bound to analytics datasets + profiles."""

    name: str
    tiles: list[DashboardTile] = field(default_factory=list)
    id: str | None = None
    title: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("DashboardDefinition name must be non-empty")

    @property
    def definition_id(self) -> str:
        return self.id if self.id else self.name

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": _DEFINITION_VERSION,
            "kind": "dashboard",
            "name": self.name,
            "id": self.definition_id,
            "title": self.title or self.name,
            "description": self.description,
            "tiles": [t.to_dict() for t in self.tiles],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardDefinition:
        tiles_raw = data.get("tiles") or []
        tiles = [
            DashboardTile.from_dict(t) for t in tiles_raw if isinstance(t, dict)
        ]
        return cls(
            name=str(data.get("name") or ""),
            id=str(data["id"]) if data.get("id") else None,
            title=str(data.get("title") or ""),
            description=str(data.get("description") or ""),
            tiles=tiles,
            metadata=dict(data.get("metadata") or {}),
        )


__all__ = ["DashboardDefinition", "DashboardTile"]
