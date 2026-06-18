"""Resource Explorer helpers — catalog filters, usage stats, and wizard integration."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from palm.common.runtimes.server.protocol import ServerRequest
from palm.definitions.flow import FlowDefinition


def catalog_filters(request: ServerRequest) -> tuple[str, str]:
    """Return ``(provider_filter, search_query)`` from query string."""
    provider = str(request.query.get("provider") or "").strip()
    query = str(request.query.get("q") or "").strip()
    return provider, query


def filter_catalog_entries(
    entries: list[Any],
    *,
    provider: str = "",
    query: str = "",
) -> list[Any]:
    """Filter catalog rows by provider name and free-text search."""
    rows = list(entries)
    if provider:
        rows = [entry for entry in rows if entry.provider == provider]
    if query:
        needle = query.lower()

        def matches(entry: Any) -> bool:
            haystack = " ".join(
                [
                    entry.name,
                    entry.provider,
                    entry.action,
                    entry.definition_id,
                    entry.summary(),
                ]
            ).lower()
            return needle in haystack

        rows = [entry for entry in rows if matches(entry)]
    return rows


def provider_options(entries: list[Any]) -> list[str]:
    """Distinct provider names for catalog filter dropdown."""
    return sorted({entry.provider for entry in entries})


def usage_counts(invocation_rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count completed invocations per ``resource_ref`` / definition name."""
    counts: dict[str, int] = {}
    for row in invocation_rows:
        if not isinstance(row, dict):
            continue
        for entry in row.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("event_type") != "resource.completed":
                continue
            key = entry.get("resource_ref") or entry.get("definition_name")
            if not key:
                continue
            counts[str(key)] = counts.get(str(key), 0) + 1
    return counts


def invocations_for_resource(
    invocation_rows: list[dict[str, Any]],
    *,
    name: str,
    definition_id: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Collect recent invocation entries matching a resource definition."""
    matches: list[dict[str, Any]] = []
    keys = {name, definition_id}
    for row in invocation_rows:
        if not isinstance(row, dict):
            continue
        for entry in row.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("resource_ref") or entry.get("definition_name")
            if ref not in keys:
                continue
            enriched = dict(entry)
            if row.get("job_id"):
                enriched["job_id"] = row["job_id"]
            if row.get("instance_id"):
                enriched["instance_id"] = row["instance_id"]
            matches.append(enriched)
    matches.sort(key=lambda item: str(item.get("recorded_at", "")), reverse=True)
    return matches[:limit]


def related_jobs(invocations: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Distinct job links from invocation entries."""
    seen: set[str] = set()
    links: list[dict[str, str]] = []
    for entry in invocations:
        job_id = entry.get("job_id")
        if not job_id or job_id in seen:
            continue
        seen.add(str(job_id))
        links.append(
            {
                "job_id": str(job_id),
                "href": f"/explorer/jobs/{quote(str(job_id), safe='')}",
            }
        )
    return links


def related_instances(invocations: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Distinct instance links from invocation entries."""
    seen: set[str] = set()
    links: list[dict[str, str]] = []
    for entry in invocations:
        instance_id = entry.get("instance_id")
        if not instance_id or instance_id in seen:
            continue
        seen.add(str(instance_id))
        links.append(
            {
                "instance_id": str(instance_id),
                "href": f"/explorer/instances/{quote(str(instance_id), safe='')}",
            }
        )
    return links


def flows_using_resource(
    flows: list[FlowDefinition],
    *,
    name: str,
    definition_id: str,
) -> list[dict[str, Any]]:
    """Flows whose wizard steps reference this resource."""
    refs = {name, definition_id}
    hits: list[dict[str, Any]] = []
    for flow in flows:
        options = flow.options or {}
        steps = options.get("steps")
        if not isinstance(steps, list):
            continue
        resource_steps: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("step_kind") != "resource":
                continue
            ref = step.get("resource_ref")
            if ref not in refs:
                continue
            resource_steps.append(step)
        if resource_steps:
            hits.append(
                {
                    "flow_id": flow.definition_id,
                    "flow_name": flow.name,
                    "pattern": flow.pattern,
                    "steps": resource_steps,
                }
            )
    return hits


def wizard_resource_steps(flow: FlowDefinition) -> list[dict[str, Any]]:
    """Return resource step dicts for a wizard flow."""
    options = flow.options or {}
    steps = options.get("steps")
    if not isinstance(steps, list):
        return []
    return [
        dict(step)
        for step in steps
        if isinstance(step, dict) and step.get("step_kind") == "resource"
    ]


def resource_href(resource_id: str) -> str:
    return f"/explorer/resources/{quote(resource_id, safe='')}"


def invoke_href(resource_id: str) -> str:
    return f"/explorer/resources/{quote(resource_id, safe='')}/invoke"


def schema_label(has_input: bool, has_output: bool) -> str:
    if has_input and has_output:
        return "in+out"
    if has_input:
        return "in"
    if has_output:
        return "out"
    return "—"


def binding_preview(params: dict[str, Any], state: dict[str, Any]) -> list[tuple[str, str]]:
    """Show how ``{{ state.* }}`` placeholders would resolve."""
    from palm.core.resource.invocation import bind_resource_params

    bound = bind_resource_params(params, state)
    preview: list[tuple[str, str]] = []
    for key, raw in params.items():
        resolved = bound.get(key, raw)
        preview.append((str(key), str(resolved)))
    return preview


def describe_provider_actions(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize provider action metadata for detail view."""
    actions: list[dict[str, str]] = []
    default_action = str(payload.get("action") or "fetch")
    provider_actions = payload.get("provider_actions") or []
    descriptions = {
        "fetch": "Read a resource by id or path",
        "submit_flow": (
            "Submit a child Palm flow (compositional). "
            "wait_mode: until_terminal | until_input | fire_and_forget"
        ),
        "submit_process": (
            "Submit a child Palm process. "
            "wait_mode: until_terminal | until_input | fire_and_forget"
        ),
        "invoke_resource": "Nested resource invocation via palm provider",
    }
    if isinstance(provider_actions, list) and provider_actions:
        for action in provider_actions:
            name = str(action)
            actions.append(
                {
                    "name": name,
                    "description": descriptions.get(name, "Provider action"),
                    "default": name == default_action,
                }
            )
    else:
        actions.append(
            {
                "name": default_action,
                "description": descriptions.get(default_action, "Default resource action"),
                "default": True,
            }
        )
    return actions


def definition_form_rows(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Human-readable definition fields for the form view."""
    rows = [
        ("Name", str(payload.get("name") or "—")),
        ("Definition ID", str(payload.get("definition_id") or "—")),
        ("Provider", str(payload.get("provider") or "—")),
        ("Default action", str(payload.get("action") or "—")),
        ("Resource ID template", str(payload.get("resource_id") or "—")),
        ("Output key", str(payload.get("output_key") or "—")),
        ("Param keys", ", ".join(payload.get("param_keys") or []) or "—"),
    ]
    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and metadata:
        rows.append(("Metadata", ", ".join(f"{k}={v}" for k, v in metadata.items())))
    return rows


def palm_invoke_chain(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build parent → child chain nodes from invocation entries with depth metadata."""
    chain: list[dict[str, Any]] = []
    for entry in entries:
        depth = entry.get("invoke_depth")
        parent = entry.get("parent_job_id")
        if depth is None and not parent:
            continue
        chain.append(
            {
                "label": entry.get("resource_ref") or entry.get("action") or "invoke",
                "action": entry.get("action"),
                "depth": depth,
                "parent_job_id": parent,
                "job_id": entry.get("job_id"),
            }
        )
    return chain
