"""
Analytics preflight probe — published-dataset health for the doctor report.

Registered into the resource preflight registry on package import (see
``palm.services.analytics.__init__``), so ``common`` never imports analytics to
compute this.
"""

from __future__ import annotations

from typing import Any

from palm.services.analytics.datasets import READ_ACTION_ALLOWLIST
from palm.services.analytics.exposure import parse_analytics_exposure


def build_analytics_preflight(repository: Any) -> dict[str, Any]:
    """Published analytics dataset health for doctor."""
    published = 0
    issues: list[str] = []
    try:
        resources = list(repository.list_resources())
    except Exception:
        return {"published_count": 0, "issues": ["repository list_resources failed"]}

    for res in resources:
        meta = getattr(res, "metadata", None) or {}
        if not isinstance(meta, dict):
            continue
        exp = parse_analytics_exposure(meta)
        if not exp.published:
            continue
        published += 1
        name = getattr(res, "name", None) or getattr(res, "definition_id", "?")
        action = str(getattr(res, "action", "") or "").lower()
        if action and action not in READ_ACTION_ALLOWLIST:
            issues.append(f"published dataset {name!r} has non-read action {action!r}")
        if exp.is_virtual and not exp.source:
            issues.append(f"virtual view {name!r} missing source")
        schema = getattr(res, "output_schema", None)
        if not schema and not exp.fields:
            issues.append(f"published dataset {name!r} has no output_schema or analytics.fields")
    return {"published_count": published, "issues": issues}


__all__ = ["build_analytics_preflight"]
