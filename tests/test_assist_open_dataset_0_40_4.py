"""0.40.4 — assist open:dataset describe + virtual transform ops."""

from __future__ import annotations

from palm.services.analytics.virtual import apply_view_transform
from palm.services.assist.catalog.open import open_target, parse_open_token


def test_parse_open_dataset_token() -> None:
    assert parse_open_token("open:dataset:palm-todos") == ("dataset", "palm-todos")


def test_virtual_filter_eq_and_limit() -> None:
    rows = [
        {"flow_name": "a", "n": 1},
        {"flow_name": "b", "n": 2},
        {"flow_name": "a", "n": 3},
    ]
    filtered = apply_view_transform(
        rows, {"op": "filter_eq", "field": "flow_name", "value": "a"}
    )
    assert len(filtered) == 2
    limited = apply_view_transform(filtered, {"op": "limit", "n": 1})
    assert len(limited) == 1
    sorted_rows = apply_view_transform(
        rows, {"op": "sort_by", "field": "n", "desc": True}
    )
    assert sorted_rows[0]["n"] == 3


def test_open_dataset_describe_with_fake_analytics() -> None:
    class _Analytics:
        def describe(self, name: str) -> dict:
            return {
                "dataset": name,
                "kind": "fact",
                "fields": [{"name": "title"}, {"name": "priority"}],
            }

        def query(self, name: str, **kwargs) -> dict:
            return {
                "dataset": name,
                "profile": kwargs.get("profile") or "table",
                "data": {"rows": [{"title": "x", "priority": "high"}]},
            }

    class _Assist:
        analytics = _Analytics()
        definitions = None

    out = open_target(_Assist(), kind="dataset", target_id="palm-todos", params={})  # type: ignore[arg-type]
    assert out["kind"] == "dataset"
    assert out["status"] == "ok"
    assert out["describe"]["dataset"] == "palm-todos"
    assert "preview" in out
