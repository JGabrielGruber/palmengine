"""0.35.2 — AnalyticsService gates, list, query normalize (fakes; no host)."""

from __future__ import annotations

from typing import Any

import pytest

from palm.services.analytics.errors import AnalyticsDisabledError
from palm.services.analytics.service import AnalyticsService


class _FakeDefinitions:
    def __init__(self, resources: dict[str, dict[str, Any]]) -> None:
        self._by_name = resources

    def list_resources(self, *, provider: str | None = None) -> list[dict[str, Any]]:
        rows = []
        for name, d in self._by_name.items():
            if provider and d.get("provider") != provider:
                continue
            rows.append(
                {
                    "name": name,
                    "definition_id": d.get("id") or name,
                    "provider": d.get("provider"),
                }
            )
        return rows

    def get_resource(self, ref: str) -> dict[str, Any]:
        from palm.common.services.errors import DefinitionNotFoundServiceError

        key = str(ref).strip()
        if key in self._by_name:
            return dict(self._by_name[key])
        for d in self._by_name.values():
            if d.get("id") == key:
                return dict(d)
        raise DefinitionNotFoundServiceError("resource", key)


class _FakeProviders:
    def __init__(self, envelopes: dict[str, dict[str, Any]]) -> None:
        self.envelopes = envelopes
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def invoke(
        self,
        resource_ref: str,
        *,
        params: dict[str, Any] | None = None,
        runtime_name: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        self.calls.append((resource_ref, params))
        if resource_ref not in self.envelopes:
            return {"success": False, "data": None, "error": "missing"}
        return self.envelopes[resource_ref]


def _svc(
    resources: dict[str, dict[str, Any]],
    envelopes: dict[str, dict[str, Any]] | None = None,
    **kwargs: Any,
) -> AnalyticsService:
    return AnalyticsService(
        definitions=_FakeDefinitions(resources),
        providers=_FakeProviders(envelopes or {}),
        **kwargs,
    )


def _pub(
    name: str,
    *,
    action: str = "get",
    kind: str = "fact",
    row_path: str | None = None,
    published: bool = True,
) -> dict[str, Any]:
    analytics: dict[str, Any] = {
        "published": published,
        "kind": kind,
        "default_profile": "table",
    }
    if row_path:
        analytics["row_path"] = row_path
    return {
        "name": name,
        "provider": "kv",
        "action": action,
        "metadata": {"analytics": analytics},
        "output_schema": None,
    }


def test_list_datasets_published_only() -> None:
    svc = _svc(
        {
            "sales": _pub("sales"),
            "secret": _pub("secret", published=False),
            "writer": _pub("writer", action="put"),
        }
    )
    rows = svc.list_datasets()
    assert [r["dataset"] for r in rows] == ["sales"]


def test_describe_unpublished_is_not_found() -> None:
    svc = _svc({"secret": _pub("secret", published=False)})
    out = svc.query("secret")
    assert out["status"] == "error"
    assert out["code"] == "dataset_not_found"


def test_put_action_forbidden() -> None:
    svc = _svc({"w": _pub("w", action="put")})
    out = svc.query("w")
    assert out["status"] == "error"
    assert out["code"] == "analytics_action_not_allowed"


def test_query_table_select_limit() -> None:
    rows_payload = [
        {"day": "2026-07-01", "revenue": 10, "x": 1},
        {"day": "2026-07-02", "revenue": 20, "x": 2},
        {"day": "2026-07-03", "revenue": 30, "x": 3},
    ]
    svc = _svc(
        {"sales": _pub("sales", row_path="items")},
        {
            "sales": {
                "success": True,
                "data": {"items": rows_payload},
                "error": None,
            }
        },
    )
    out = svc.query("sales", profile="table", select=["day", "revenue"], limit=2)
    assert out["status"] == "ok"
    assert out["data"]["columns"] == ["day", "revenue"]
    assert len(out["data"]["rows"]) == 2
    assert out["meta"]["truncated"] is True
    assert out["meta"]["row_count"] == 2


def test_query_raw_skips_select() -> None:
    svc = _svc(
        {"sales": _pub("sales")},
        {"sales": {"success": True, "data": {"hello": 1}, "error": None}},
    )
    out = svc.query("sales", profile="raw", select=["nope"])
    assert out["status"] == "ok"
    assert out["data"]["payload"] == {"hello": 1}


def test_disabled_raises() -> None:
    svc = _svc({"sales": _pub("sales")}, enabled=False)
    with pytest.raises(AnalyticsDisabledError):
        svc.list_datasets()


def test_allow_unpublished() -> None:
    svc = _svc(
        {"secret": _pub("secret", published=False)},
        {"secret": {"success": True, "data": [{"a": 1}], "error": None}},
        allow_unpublished=True,
    )
    out = svc.query("secret", profile="table")
    assert out["status"] == "ok"
    assert out["data"]["rows"] == [[1]]


def test_query_series_and_kpi() -> None:
    payload = [
        {"day": "d1", "revenue": 10},
        {"day": "d2", "revenue": 30},
    ]
    svc = _svc(
        {"sales": _pub("sales")},
        {"sales": {"success": True, "data": payload, "error": None}},
    )
    s = svc.query(
        "sales",
        profile="series",
        series={"x_field": "day", "y_fields": ["revenue"]},
    )
    assert s["status"] == "ok"
    assert s["data"]["series"][0]["points"][-1] == ["d2", 30]
    k = svc.query("sales", profile="kpi", kpi={"field": "revenue", "agg": "sum"})
    assert k["status"] == "ok"
    assert k["data"]["value"] == 40.0
    assert k["data"]["delta"] is None
