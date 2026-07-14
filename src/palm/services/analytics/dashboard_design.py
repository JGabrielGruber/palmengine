"""Validate and build dashboard definitions for design commit (0.41.2)."""

from __future__ import annotations

from typing import Any

from palm.definitions.dashboard import DashboardDefinition, DashboardTile

_PROFILES = frozenset({"raw", "table", "series", "kpi"})


def extract_dashboard_dict(body: dict[str, Any]) -> dict[str, Any] | None:
    """Inner dashboard payload from a proposal envelope."""
    section = body.get("dashboard")
    if isinstance(section, dict):
        return section
    if body.get("kind") == "dashboard" or "tiles" in body:
        return body
    return None


def resolve_dashboard_name(
    body: dict[str, Any],
    *,
    base_name: str | None = None,
) -> str | None:
    if base_name:
        return str(base_name).strip() or None
    payload = extract_dashboard_dict(body) or body
    for key in ("name", "id", "dashboard_id", "dashboard_name"):
        value = payload.get(key)
        if value:
            return str(value).strip()
    return None


def validate_dashboard_body(
    body: dict[str, Any],
    *,
    known_datasets: set[str] | None = None,
) -> tuple[bool, list[str], DashboardDefinition | None]:
    """
    Structural validation (+ optional dataset existence).

    Returns ``(ok, blockers, parsed_or_none)``.
    """
    blockers: list[str] = []
    payload = extract_dashboard_dict(body)
    if payload is None:
        return False, ["body must include dashboard fields or kind=dashboard"], None

    name = resolve_dashboard_name(payload)
    if not name:
        blockers.append("dashboard name is required")

    tiles_raw = payload.get("tiles")
    if not isinstance(tiles_raw, list) or not tiles_raw:
        blockers.append("dashboard must have at least one tile")
        tiles_raw = []

    tiles: list[DashboardTile] = []
    seen_ids: set[str] = set()
    for i, raw in enumerate(tiles_raw):
        if not isinstance(raw, dict):
            blockers.append(f"tiles[{i}] must be an object")
            continue
        tid = str(raw.get("id") or f"tile-{i + 1}").strip()
        dataset = str(raw.get("dataset") or "").strip()
        profile = str(raw.get("profile") or "table").strip().lower()
        if not dataset:
            blockers.append(f"tiles[{i}] ({tid}): dataset is required")
        if profile not in _PROFILES:
            blockers.append(
                f"tiles[{i}] ({tid}): profile must be one of {sorted(_PROFILES)}"
            )
        if tid in seen_ids:
            blockers.append(f"duplicate tile id: {tid}")
        seen_ids.add(tid)
        if known_datasets is not None and dataset and dataset not in known_datasets:
            blockers.append(
                f"tiles[{i}] ({tid}): unknown dataset {dataset!r} "
                "(publish resource with analytics.published or register origin dataset)"
            )
        if profile == "series":
            series = raw.get("series")
            if series is not None and not isinstance(series, dict):
                blockers.append(f"tiles[{i}] ({tid}): series must be an object")
        if profile == "kpi":
            kpi = raw.get("kpi")
            if kpi is not None and not isinstance(kpi, dict):
                blockers.append(f"tiles[{i}] ({tid}): kpi must be an object")
        try:
            tiles.append(
                DashboardTile(
                    id=tid or f"tile-{i + 1}",
                    dataset=dataset or "_missing_",
                    profile=profile if profile in _PROFILES else "table",
                    title=str(raw.get("title") or ""),
                    options=dict(raw.get("options") or {})
                    if isinstance(raw.get("options"), dict)
                    else {},
                    select=list(raw["select"])
                    if isinstance(raw.get("select"), list)
                    else None,
                    limit=int(raw["limit"]) if raw.get("limit") is not None else None,
                    series=dict(raw["series"])
                    if isinstance(raw.get("series"), dict)
                    else None,
                    kpi=dict(raw["kpi"]) if isinstance(raw.get("kpi"), dict) else None,
                )
            )
        except (TypeError, ValueError) as exc:
            blockers.append(f"tiles[{i}]: {exc}")

    if blockers or not name:
        return False, blockers, None

    dash = DashboardDefinition(
        name=name,
        id=str(payload["id"]) if payload.get("id") else None,
        title=str(payload.get("title") or name),
        description=str(payload.get("description") or ""),
        tiles=tiles,
        metadata=dict(payload.get("metadata") or {}),
    )
    return True, [], dash


def validate_dashboard_design_proposal(
    body: dict[str, Any],
    context: Any,
) -> tuple[bool, list[str]]:
    """DesignContributor hook — only when body is a dashboard proposal."""
    if extract_dashboard_dict(body) is None and body.get("kind") != "dashboard":
        return True, []
    known: set[str] | None = None
    analytics = getattr(context, "analytics", None)
    if analytics is None and hasattr(context, "_analytics"):
        analytics = getattr(context, "_analytics", None)
    # DesignService may not hold analytics; skip dataset existence then
    if analytics is not None and hasattr(analytics, "list_datasets"):
        try:
            rows = analytics.list_datasets() or []
            known = {
                str(r.get("name") or r.get("dataset") or "")
                for r in rows
                if isinstance(r, dict)
            }
            known.discard("")
        except Exception:
            known = None
    ok, blockers, _ = validate_dashboard_body(body, known_datasets=known)
    return ok, blockers


__all__ = [
    "extract_dashboard_dict",
    "resolve_dashboard_name",
    "validate_dashboard_body",
    "validate_dashboard_design_proposal",
]
