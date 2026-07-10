# ADR-014: Dashboard Definitions (0.39)

## Status

**Accepted** — July 2026

## Context

0.35–0.36 shipped AnalyticsService (query + present profiles) and a static dogfood UI that hard-codes table+chart. Operators need **named layouts** of tiles without putting join/query logic in the browser or inventing a second brain.

## Decision

1. **`DashboardDefinition` + `DashboardTile`** live in `palm.definitions` as pure contracts.
2. Tiles bind **dataset + profile + options** (`select`, `limit`, `series`, `kpi`) only.
3. **Render** = loop tiles → `AnalyticsService.query` (no joins).
4. **Registry** starts in-process (`analytics.dashboards`) for dogfood; durable repository can follow without changing the contract.
5. REST: `GET /v1/api/analytics/dashboards`, `…/{name}`, `…/{name}/render`.
6. Thin static UI loads dashboards by name; optional `?dashboard=`.

## Consequences

- Examples register dashboards next to resource packs (`todos/dashboard.py`).
- Design-service authoring of dashboards is deferred (0.39.3 optional).
- Aligns with VISION-0.36 present-profile philosophy.

## References

- [VISION-0.36](../VISION-0.36.md)
- `palm/definitions/dashboard.py`, `palm/services/analytics/dashboards.py`
