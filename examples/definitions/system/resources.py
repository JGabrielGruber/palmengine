"""
Published system datasets — ``provider: palm`` system-read actions.

Same resources work against a remote Palm via params.remote_url on invoke
or by overriding resource params when querying.
"""

from __future__ import annotations

from palm.definitions import ResourceDefinition

_PALM = "palm"


def _sys(
    name: str,
    action: str,
    *,
    title: str,
    kind: str = "fact",
    profile: str = "table",
) -> ResourceDefinition:
    return ResourceDefinition(
        id=f"resource-{name}",
        name=name,
        provider=_PALM,
        action=action,
        resource_id=action,
        params={},
        metadata={
            "description": title,
            "tags": ["palm", "system", "ops", "bi"],
            "analytics": {
                "published": True,
                "kind": kind,
                "default_profile": profile,
                "row_path": "items",
            },
        },
    )


PALM_SYSTEM_JOBS = _sys(
    "palm-system-jobs",
    "list_jobs",
    title="Jobs on this (or remote) Palm",
)
PALM_SYSTEM_WAITING = _sys(
    "palm-system-waiting",
    "list_waiting",
    title="Jobs waiting for input",
)
PALM_SYSTEM_INSTANCES = _sys(
    "palm-system-instances",
    "list_instances",
    title="Durable instances",
)
PALM_SYSTEM_FLOWS = _sys(
    "palm-system-flows",
    "list_flows",
    title="Flow catalog",
)
PALM_SYSTEM_RESOURCES = _sys(
    "palm-system-resources",
    "list_resources",
    title="Resource catalog",
)


def register_definitions(repository: object) -> None:
    save = getattr(repository, "save_resource", None)
    if not callable(save):
        return
    for res in (
        PALM_SYSTEM_JOBS,
        PALM_SYSTEM_WAITING,
        PALM_SYSTEM_INSTANCES,
        PALM_SYSTEM_FLOWS,
        PALM_SYSTEM_RESOURCES,
    ):
        save(res)


__all__ = [
    "PALM_SYSTEM_FLOWS",
    "PALM_SYSTEM_INSTANCES",
    "PALM_SYSTEM_JOBS",
    "PALM_SYSTEM_RESOURCES",
    "PALM_SYSTEM_WAITING",
    "register_definitions",
]
