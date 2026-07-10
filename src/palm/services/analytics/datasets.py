"""Dataset resolve + list (public DefinitionService N+1)."""

from __future__ import annotations

from typing import Any

from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.analytics.errors import (
    AnalyticsActionNotAllowedError,
    DatasetNotFoundError,
)
from palm.services.analytics.exposure import (
    AnalyticsExposure,
    parse_analytics_exposure,
)

# Read-only provider actions safe for BI query (no client override of definition action).
READ_ACTION_ALLOWLIST = frozenset(
    {
        "get",
        "list",
        "fetch",
        "read",
        "exists",
    }
)


def action_is_bi_safe(action: str | None) -> bool:
    return str(action or "").strip().lower() in READ_ACTION_ALLOWLIST


def resolve_dataset(
    definitions: Any,
    ref: str,
    *,
    allow_unpublished: bool = False,
) -> tuple[dict[str, Any], AnalyticsExposure]:
    """Resolve name-then-id; 404 for missing/unpublished; 403 for non-read action."""
    key = str(ref or "").strip()
    if not key:
        raise DatasetNotFoundError(ref or "")

    detail = _get_resource(definitions, key)
    if detail is None:
        raise DatasetNotFoundError(key)

    exposure = parse_analytics_exposure(detail.get("metadata"))
    if not exposure.published and not allow_unpublished:
        raise DatasetNotFoundError(key)

    action = str(detail.get("action") or "")
    if not action_is_bi_safe(action):
        raise AnalyticsActionNotAllowedError(key, action)

    return detail, exposure


def list_datasets(
    definitions: Any,
    *,
    published_only: bool = True,
) -> list[dict[str, Any]]:
    """N+1 list via public DefinitionService (thin list + get_resource)."""
    rows = definitions.list_resources() or []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("definition_id") or "").strip()
        if not name:
            continue
        detail = _get_resource(definitions, name)
        if detail is None:
            continue
        exposure = parse_analytics_exposure(detail.get("metadata"))
        if published_only and not exposure.published:
            continue
        action = str(detail.get("action") or "")
        if not action_is_bi_safe(action):
            continue
        dataset = str(detail.get("name") or name)
        out.append(
            {
                "dataset": dataset,
                "kind": exposure.kind,
                "provider": detail.get("provider"),
                "action": action,
                "default_profile": exposure.default_profile,
                "derived_from": list(exposure.derived_from),
            }
        )
    return out


def _get_resource(definitions: Any, ref: str) -> dict[str, Any] | None:
    get = getattr(definitions, "get_resource", None)
    if not callable(get):
        return None
    try:
        detail = get(ref)
    except (DefinitionNotFoundServiceError, LookupError, KeyError):
        return None
    return detail if isinstance(detail, dict) else None


__all__ = [
    "READ_ACTION_ALLOWLIST",
    "action_is_bi_safe",
    "list_datasets",
    "resolve_dataset",
]
