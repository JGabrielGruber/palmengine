"""0.35.3 — pure present profiles."""

from __future__ import annotations

from palm.services.analytics.present.pipeline import present
from palm.services.analytics.present.profiles.kpi import present_kpi
from palm.services.analytics.present.profiles.series import present_series
from palm.services.analytics.present.profiles.table import present_table


def test_table() -> None:
    d = present_table([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    assert d["columns"] == ["a", "b"]
    assert d["rows"] == [[1, 2], [3, 4]]


def test_series_defaults() -> None:
    rows = [{"day": "d1", "revenue": 10, "orders": 2}, {"day": "d2", "revenue": 20, "orders": 3}]
    d = present_series(rows)
    assert d["x_field"] == "day"
    names = {s["name"] for s in d["series"]}
    assert "revenue" in names
    rev = next(s for s in d["series"] if s["name"] == "revenue")
    assert rev["points"][0] == ["d1", 10]


def test_series_explicit() -> None:
    rows = [{"x": 1, "y": 9, "z": 0}]
    d = present_series(rows, x_field="x", y_fields=["y"])
    assert d["series"] == [{"name": "y", "points": [[1, 9]]}]


def test_kpi_sum() -> None:
    d = present_kpi([{"v": 1}, {"v": 2}, {"v": 3}], field="v", agg="sum")
    assert d["value"] == 6.0
    assert d["delta"] is None


def test_kpi_count() -> None:
    d = present_kpi([{"a": 1}, {"a": 2}], agg="count")
    assert d["value"] == 2.0


def test_pipeline_dispatch() -> None:
    rows = [{"day": "a", "n": 5}]
    assert present("table", rows=rows)["columns"] == ["day", "n"]
    assert present("series", rows=rows, series={"x_field": "day", "y_fields": ["n"]})[
        "series"
    ][0]["name"] == "n"
    assert present("kpi", rows=rows, kpi={"field": "n", "agg": "max"})["value"] == 5.0
    assert present("raw", payload={"z": 1})["payload"] == {"z": 1}
