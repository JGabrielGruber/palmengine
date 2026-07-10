"""
Analytics BI dogfood (0.35.5) — materialize fact + view into kv, query via AnalyticsService.

Synthetic sales rows (no PII). Write resources are unpublished; read resources are published.

```python
register_definitions(repository)
materialize_analytics_dogfood(host.execution.providers)
host.analytics.query("sales-facts-daily", profile="table")
host.analytics.query("sales-revenue-by-day", profile="series", series={"x_field": "day", "y_fields": ["revenue"]})
```
"""

from __future__ import annotations

from typing import Any

from palm.definitions import ResourceDefinition

# Synthetic seed — materialize only (not form entry).
SEED_SALES_ROWS: list[dict[str, Any]] = [
    {"day": "2026-07-01", "revenue": 1200.5, "orders": 14, "region": "north"},
    {"day": "2026-07-02", "revenue": 980.0, "orders": 11, "region": "south"},
    {"day": "2026-07-03", "revenue": 1505.25, "orders": 18, "region": "north"},
]

_NS = "analytics"
_BACKEND = "memory"

PUT_SALES_FACTS = ResourceDefinition(
    id="resource-put-sales-facts-daily",
    name="put-sales-facts-daily",
    provider="kv",
    action="put",
    resource_id="facts/sales-daily",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Write sales fact payload (operator/materialize only)",
        "tags": ["analytics", "kv", "write"],
    },
)

SALES_FACTS_DAILY = ResourceDefinition(
    id="resource-sales-facts-daily",
    name="sales-facts-daily",
    provider="kv",
    action="get",
    resource_id="facts/sales-daily",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Daily sales fact rows (BI published)",
        "tags": ["analytics", "bi", "fact"],
        "analytics": {
            "published": True,
            "kind": "fact",
            "default_profile": "table",
            "row_path": "value.items",
            "refresh": {"note": "call materialize_analytics_dogfood"},
        },
    },
)

PUT_SALES_REVENUE = ResourceDefinition(
    id="resource-put-sales-revenue-by-day",
    name="put-sales-revenue-by-day",
    provider="kv",
    action="put",
    resource_id="views/sales-revenue-by-day",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Write revenue-by-day view payload",
        "tags": ["analytics", "kv", "write"],
    },
)

SALES_REVENUE_BY_DAY = ResourceDefinition(
    id="resource-sales-revenue-by-day",
    name="sales-revenue-by-day",
    provider="kv",
    action="get",
    resource_id="views/sales-revenue-by-day",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Materialized revenue by day (BI published view)",
        "tags": ["analytics", "bi", "view"],
        "analytics": {
            "published": True,
            "kind": "view",
            "derived_from": ["sales-facts-daily"],
            "default_profile": "series",
            "row_path": "value.items",
        },
    },
)


def register_definitions(repository: object) -> None:
    save = getattr(repository, "save_resource", None)
    if not callable(save):
        return
    for res in (
        PUT_SALES_FACTS,
        SALES_FACTS_DAILY,
        PUT_SALES_REVENUE,
        SALES_REVENUE_BY_DAY,
    ):
        save(res)


def materialize_analytics_dogfood(
    providers: Any,
    *,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Put fact + derived view into kv via unpublished write resources."""
    seed = list(rows if rows is not None else SEED_SALES_ROWS)
    fact_body = {"items": seed}
    view_body = {
        "items": [
            {"day": r["day"], "revenue": r["revenue"]}
            for r in seed
            if "day" in r and "revenue" in r
        ]
    }
    fact_put = providers.invoke(
        "put-sales-facts-daily",
        params={"value": fact_body},
    )
    view_put = providers.invoke(
        "put-sales-revenue-by-day",
        params={"value": view_body},
    )
    return {
        "fact_rows": len(seed),
        "view_rows": len(view_body["items"]),
        "fact_put": fact_put,
        "view_put": view_put,
    }


__all__ = [
    "PUT_SALES_FACTS",
    "PUT_SALES_REVENUE",
    "SALES_FACTS_DAILY",
    "SALES_REVENUE_BY_DAY",
    "SEED_SALES_ROWS",
    "materialize_analytics_dogfood",
    "register_definitions",
]
