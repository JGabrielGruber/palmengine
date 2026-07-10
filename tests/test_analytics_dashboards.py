"""0.39 — DashboardDefinition + render."""

from __future__ import annotations

from typing import Any

from palm.definitions.dashboard import DashboardDefinition, DashboardTile
from palm.services.analytics.dashboards import (
    clear_dashboards,
    list_dashboards,
    register_dashboard,
    render_dashboard,
)
from palm.services.analytics.service import AnalyticsService


class _FakeDefinitions:
    def __init__(self, resources: dict[str, dict[str, Any]]) -> None:
        self._by_name = resources

    def list_resources(self, **_: Any) -> list[dict[str, Any]]:
        return [{"name": n, "provider": d.get("provider")} for n, d in self._by_name.items()]

    def get_resource(self, ref: str) -> dict[str, Any]:
        from palm.common.services.errors import DefinitionNotFoundServiceError

        if ref in self._by_name:
            return dict(self._by_name[ref])
        raise DefinitionNotFoundServiceError("resource", ref)


class _FakeProviders:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def invoke(self, resource_ref: str, **_: Any) -> dict[str, Any]:
        self.calls.append(resource_ref)
        if resource_ref == "palm-todos":
            return {
                "success": True,
                "data": {
                    "value": [
                        {"title": "a", "priority": "high", "due_date": ""},
                        {"title": "b", "priority": "low", "due_date": ""},
                    ]
                },
                "error": None,
            }
        return {"success": False, "data": None, "error": "missing"}


def test_register_list_render_dashboard() -> None:
    clear_dashboards()
    register_dashboard(
        DashboardDefinition(
            name="palm-todos",
            title="Todos",
            tiles=[
                DashboardTile(
                    id="t1",
                    dataset="palm-todos",
                    profile="table",
                    select=["title", "priority"],
                ),
                DashboardTile(
                    id="t2",
                    dataset="palm-todos-by-priority",
                    profile="series",
                    series={"x_field": "priority", "y_fields": ["count"]},
                ),
            ],
        )
    )
    assert any(d["name"] == "palm-todos" for d in list_dashboards())

    resources = {
        "palm-todos": {
            "name": "palm-todos",
            "provider": "kv",
            "action": "get",
            "metadata": {
                "analytics": {
                    "published": True,
                    "kind": "fact",
                    "row_path": "value",
                }
            },
        },
        "palm-todos-by-priority": {
            "name": "palm-todos-by-priority",
            "provider": "kv",
            "action": "get",
            "metadata": {
                "analytics": {
                    "published": True,
                    "kind": "view",
                    "source": "palm-todos",
                    "materialize": False,
                    "transform": {"op": "count_by", "field": "priority"},
                }
            },
        },
    }
    svc = AnalyticsService(
        definitions=_FakeDefinitions(resources),
        providers=_FakeProviders(),
    )
    out = render_dashboard(svc, "palm-todos")
    assert out["status"] == "ok"
    assert len(out["tiles"]) == 2
    assert out["tiles"][0]["result"]["status"] == "ok"
    assert out["tiles"][1]["result"]["status"] == "ok"
    assert out["tiles"][1]["result"]["meta"].get("virtual") is True
    clear_dashboards()


def test_dashboard_roundtrip_dict() -> None:
    d = DashboardDefinition.from_dict(
        {
            "name": "x",
            "tiles": [{"id": "1", "dataset": "d", "profile": "kpi"}],
        }
    )
    assert d.tiles[0].profile == "kpi"
    assert d.to_dict()["kind"] == "dashboard"
