"""0.35.5 — analytics dogfood materialize + query."""

from __future__ import annotations

from examples.definitions.analytics_dogfood import (
    SEED_SALES_ROWS,
    materialize_analytics_dogfood,
    register_definitions,
)
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings


def test_materialize_and_query_fact_and_view() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=HostProfile.all_in_one(),
    ) as host:
        register_definitions(host.app.repository())
        result = materialize_analytics_dogfood(host.execution.providers)
        assert result["fact_rows"] == len(SEED_SALES_ROWS)
        assert result["fact_put"].get("success") is True
        assert result["view_put"].get("success") is True

        names = {r["dataset"] for r in host.analytics.list_datasets()}
        assert "sales-facts-daily" in names
        assert "sales-revenue-by-day" in names

        table = host.analytics.query(
            "sales-facts-daily",
            profile="table",
            select=["day", "revenue", "orders"],
        )
        assert table["status"] == "ok", table
        assert table["data"]["columns"] == ["day", "revenue", "orders"]
        assert len(table["data"]["rows"]) == 3
        assert table["lineage"]["kind"] == "fact"

        series = host.analytics.query(
            "sales-revenue-by-day",
            profile="series",
            series={"x_field": "day", "y_fields": ["revenue"]},
        )
        assert series["status"] == "ok", series
        assert series["lineage"]["kind"] == "view"
        assert series["lineage"]["derived_from"] == ["sales-facts-daily"]
        points = series["data"]["series"][0]["points"]
        assert points[0][0] == "2026-07-01"
        assert points[0][1] == 1200.5

        kpi = host.analytics.query(
            "sales-revenue-by-day",
            profile="kpi",
            kpi={"field": "revenue", "agg": "sum"},
        )
        assert kpi["status"] == "ok"
        assert kpi["data"]["value"] == 1200.5 + 980.0 + 1505.25
