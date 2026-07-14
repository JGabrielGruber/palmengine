"""
Origin (remote) Palm as **resources** — not analytics query params.

Proper Palm usage::

    ResourceDefinition(
        name="origin-system-flows",
        provider="palm",
        action="list_flows",
        params={"remote_url": "https://b.example"},  # origin is part of the contract
    )

Analytics / dashboards only name the dataset::

    host.analytics.query("origin-system-flows", profile="table")

Optional env (register at pack load)::

    PALM_ORIGIN_URL=https://b.example
    PALM_ORIGIN_TOKEN=…          # optional
    PALM_ORIGIN_PREFIX=origin    # default; resources are {prefix}-system-*
"""

from __future__ import annotations

import os
from typing import Any

from palm.definitions import ResourceDefinition

_PALM = "palm"
_DEFAULT_PREFIX = "origin"


def _origin_params(
    remote_url: str,
    *,
    remote_token: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"remote_url": str(remote_url).rstrip("/")}
    if remote_token:
        params["remote_token"] = str(remote_token)
    return params


def make_origin_system_resources(
    remote_url: str,
    *,
    name_prefix: str = _DEFAULT_PREFIX,
    remote_token: str | None = None,
) -> list[ResourceDefinition]:
    """Build published system datasets that always target *remote_url* via palm provider."""
    prefix = (name_prefix or _DEFAULT_PREFIX).strip().rstrip("-") or _DEFAULT_PREFIX
    params = _origin_params(remote_url, remote_token=remote_token)
    origin = params["remote_url"]

    def _fact(action: str, short: str, title: str) -> ResourceDefinition:
        name = f"{prefix}-system-{short}"
        return ResourceDefinition(
            id=f"resource-{name}",
            name=name,
            provider=_PALM,
            action=action,
            resource_id=action,
            params=dict(params),
            metadata={
                "description": f"{title} (origin Palm @ {origin})",
                "tags": ["palm", "system", "ops", "bi", "origin", "remote"],
                "analytics": {
                    "published": True,
                    "kind": "fact",
                    "default_profile": "table",
                    "row_path": "items",
                },
                "origin": {"remote_url": origin},
            },
        )

    instances_name = f"{prefix}-system-instances"
    per_flow_name = f"{prefix}-system-instances-per-flow"

    facts = [
        _fact("list_jobs", "jobs", "Jobs"),
        _fact("list_waiting", "waiting", "Jobs waiting for input"),
        _fact("list_instances", "instances", "Durable instances"),
        _fact("list_flows", "flows", "Flow catalog"),
        _fact("list_resources", "resources", "Resource catalog"),
    ]

    per_flow = ResourceDefinition(
        id=f"resource-{per_flow_name}",
        name=per_flow_name,
        provider=_PALM,
        action="list_instances",
        resource_id="list_instances",
        params=dict(params),  # unused when virtual; documents origin
        metadata={
            "description": f"Instance counts per flow on origin @ {origin}",
            "tags": ["palm", "system", "ops", "bi", "view", "origin", "remote"],
            "analytics": {
                "published": True,
                "kind": "view",
                "source": instances_name,
                "materialize": False,
                "transform": {"op": "count_by", "field": "flow_name"},
                "derived_from": [instances_name],
                "default_profile": "series",
                "fields": [
                    {"name": "flow_name", "role": "dimension"},
                    {"name": "count", "role": "measure", "type": "integer"},
                ],
            },
            "origin": {"remote_url": origin},
        },
    )
    return [*facts, per_flow]


def register_origin_system_resources(
    repository: object,
    remote_url: str,
    *,
    name_prefix: str = _DEFAULT_PREFIX,
    remote_token: str | None = None,
) -> list[str]:
    """Save origin resources; return dataset names."""
    save = getattr(repository, "save_resource", None)
    if not callable(save):
        return []
    names: list[str] = []
    for res in make_origin_system_resources(
        remote_url,
        name_prefix=name_prefix,
        remote_token=remote_token,
    ):
        save(res)
        names.append(res.name)
    return names


def register_origin_from_env(repository: object) -> list[str]:
    """If ``PALM_ORIGIN_URL`` is set, register ``{prefix}-system-*`` origin resources."""
    url = (os.environ.get("PALM_ORIGIN_URL") or "").strip()
    if not url:
        return []
    token = (os.environ.get("PALM_ORIGIN_TOKEN") or "").strip() or None
    prefix = (os.environ.get("PALM_ORIGIN_PREFIX") or _DEFAULT_PREFIX).strip()
    return register_origin_system_resources(
        repository,
        url,
        name_prefix=prefix or _DEFAULT_PREFIX,
        remote_token=token,
    )


__all__ = [
    "make_origin_system_resources",
    "register_origin_from_env",
    "register_origin_system_resources",
]
