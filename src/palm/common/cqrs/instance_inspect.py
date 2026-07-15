"""
Instance inspect dispatch — pattern-aware views without importing pattern packages.
"""

from __future__ import annotations

from typing import Any

from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    GetJobContextQuery,
    InspectInstanceQuery,
)


def handle_inspect_instance(query: InspectInstanceQuery, ctx: Any) -> dict[str, Any] | None:
    """Resolve a rich instance view via pattern CQRS contributors, then fall back."""
    import palm.patterns  # noqa: F401 — ensure contributors are registered
    from palm.common.patterns._registry import iter_cqrs_contributors

    for contributor in iter_cqrs_contributors():
        status_query = contributor.instance_status_query
        if status_query is None or contributor.handle_query is None:
            continue
        view = contributor.handle_query(status_query(instance_id=query.instance_id), ctx)
        if view is not None:
            return view if isinstance(view, dict) else view.to_dict()

    instance = _resolve_instance(query.instance_id, ctx)
    if instance is None:
        return None

    payload = instance if isinstance(instance, dict) else instance.to_dict()
    job_id = str(payload.get("job_id") or query.instance_id)
    context = _resolve_job_context(job_id, ctx)
    if isinstance(context, dict) and context.get("found") is False:
        return payload
    return context if isinstance(context, dict) else payload


def _resolve_instance(instance_id: str, ctx: Any) -> Any:
    status_query = GetInstanceStatusQuery(instance_id=instance_id)
    instances = getattr(ctx, "_instances", None)
    if instances is not None:
        return instances.get_instance(status_query)
    get_instance = getattr(ctx, "_get_instance", None)
    if callable(get_instance):
        return get_instance(status_query)
    ask = getattr(ctx, "ask", None)
    if callable(ask):
        return ask(status_query)
    return None


def _resolve_job_context(job_id: str, ctx: Any) -> Any:
    context_query = GetJobContextQuery(job_id=job_id)
    get_context = getattr(ctx, "_get_job_context", None)
    if callable(get_context):
        return get_context(context_query)
    ask = getattr(ctx, "ask", None)
    if callable(ask):
        return ask(context_query)
    return None


__all__ = ["handle_inspect_instance"]
