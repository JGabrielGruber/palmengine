"""0.36 — virtual view transform + query."""

from __future__ import annotations

from typing import Any

import pytest

from palm.services.analytics.service import AnalyticsService
from palm.services.analytics.virtual import apply_view_transform


def test_apply_count_by() -> None:
    rows = [
        {"title": "a", "priority": "high"},
        {"title": "b", "priority": "low"},
        {"title": "c", "priority": "high"},
    ]
    out = apply_view_transform(rows, {"op": "count_by", "field": "priority"})
    assert out == [
        {"priority": "high", "count": 2},
        {"priority": "low", "count": 1},
    ]


def test_unknown_op_raises() -> None:
    with pytest.raises(ValueError, match="op"):
        apply_view_transform([], {"op": "nope"})


class _FakeDefinitions:
    def __init__(self, resources: dict[str, dict[str, Any]]) -> None:
        self._by_name = resources

    def list_resources(self, *, provider: str | None = None) -> list[dict[str, Any]]:
        return [
            {"name": n, "definition_id": n, "provider": d.get("provider")}
            for n, d in self._by_name.items()
        ]

    def get_resource(self, ref: str) -> dict[str, Any]:
        from palm.common.services.errors import DefinitionNotFoundServiceError

        if ref in self._by_name:
            return dict(self._by_name[ref])
        raise DefinitionNotFoundServiceError("resource", ref)


class _FakeProviders:
    def __init__(self, envelopes: dict[str, dict[str, Any]]) -> None:
        self.envelopes = envelopes
        self.calls: list[str] = []

    def invoke(self, resource_ref: str, **_: Any) -> dict[str, Any]:
        self.calls.append(resource_ref)
        return self.envelopes.get(
            resource_ref, {"success": False, "data": None, "error": "missing"}
        )


def test_query_virtual_view_loads_source_not_self() -> None:
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
                    "default_profile": "series",
                }
            },
        },
    }
    providers = _FakeProviders(
        {
            "palm-todos": {
                "success": True,
                "data": {
                    "value": [
                        {"title": "a", "priority": "high"},
                        {"title": "b", "priority": "high"},
                    ]
                },
                "error": None,
            }
        }
    )
    svc = AnalyticsService(
        definitions=_FakeDefinitions(resources),
        providers=providers,
    )
    out = svc.query("palm-todos-by-priority", profile="table")
    assert out["status"] == "ok", out
    assert out["meta"].get("virtual") is True
    assert out["data"]["columns"] == ["priority", "count"]
    assert out["data"]["rows"] == [["high", 2]]
    assert providers.calls == ["palm-todos"]
