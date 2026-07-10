"""present(payload_or_rows, profile, options) entry."""

from __future__ import annotations

from typing import Any

from palm.services.analytics.present.profiles.kpi import present_kpi
from palm.services.analytics.present.profiles.raw import present_raw
from palm.services.analytics.present.profiles.series import present_series
from palm.services.analytics.present.profiles.table import present_table


def present(
    profile: str,
    *,
    payload: Any = None,
    rows: list[dict[str, Any]] | None = None,
    series: dict[str, Any] | None = None,
    kpi: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure reshape. ``raw`` uses ``payload``; others use post-select/limit ``rows``."""
    p = str(profile or "table").strip().lower()
    if p == "raw":
        return present_raw(payload)
    r = list(rows or [])
    if p == "table":
        return present_table(r)
    if p == "series":
        opts = series or {}
        y = opts.get("y_fields")
        if isinstance(y, str):
            y = [y]
        return present_series(
            r,
            x_field=opts.get("x_field") or opts.get("x"),
            y_fields=list(y) if isinstance(y, list) else None,
        )
    if p == "kpi":
        opts = kpi or {}
        return present_kpi(
            r,
            field=opts.get("field"),
            agg=str(opts.get("agg") or "sum"),
            label=opts.get("label"),
            unit=opts.get("unit"),
        )
    raise ValueError(f"Unknown analytics profile: {profile!r}")


__all__ = ["present"]
