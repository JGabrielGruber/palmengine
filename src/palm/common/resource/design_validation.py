"""Shared resource design validation for local document providers."""

from __future__ import annotations

import re

from palm.definitions.resource import ResourceDefinition

_KV_ACTIONS = frozenset({"get", "put", "delete", "list"})
_KV_BACKENDS = frozenset({"auto", "memory", "storage"})
_FILE_ACTIONS = frozenset({"read", "write", "delete", "exists", "list"})
_NAMESPACE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def validate_kv_resource(resource: ResourceDefinition) -> list[str]:
    """Return blocker messages for a ``kv`` resource definition."""
    blockers: list[str] = []
    action = str(resource.action or "").strip().lower()
    if action not in _KV_ACTIONS:
        blockers.append(
            f"kv resource {resource.name!r} action must be one of "
            f"{sorted(_KV_ACTIONS)}, got {resource.action!r}",
        )

    params = dict(resource.params or {})
    backend = str(params.get("backend") or "auto").strip().lower()
    if backend not in _KV_BACKENDS:
        blockers.append(
            f"kv resource {resource.name!r} params.backend must be "
            f"auto, memory, or storage (got {backend!r})",
        )

    namespace = str(params.get("namespace") or "default").strip()
    if not _NAMESPACE_RE.match(namespace):
        blockers.append(
            f"kv resource {resource.name!r} params.namespace {namespace!r} "
            "must be a slug (alphanumeric, underscore, hyphen)",
        )

    if action in {"get", "put", "delete"} and not str(resource.resource_id or "").strip():
        blockers.append(f"kv resource {resource.name!r} requires resource_id for action {action!r}")

    if action == "put" and params.get("value") is None:
        blockers.append(
            f"kv resource {resource.name!r} action put requires params.value "
            "(or a {{ state.* }} binding)",
        )

    if action == "list" and params.get("prefix") is not None:
        prefix = str(params.get("prefix"))
        if "/" in prefix or "\\" in prefix or ":" in prefix:
            blockers.append(
                f"kv resource {resource.name!r} params.prefix must not contain path separators",
            )

    return blockers


def validate_file_resource(resource: ResourceDefinition) -> list[str]:
    """Return blocker messages for a ``file`` document resource definition."""
    blockers: list[str] = []
    action = str(resource.action or "").strip().lower()
    if action not in _FILE_ACTIONS:
        blockers.append(
            f"file resource {resource.name!r} action must be one of "
            f"{sorted(_FILE_ACTIONS)}, got {resource.action!r}",
        )

    resource_id = str(resource.resource_id or "").strip()
    if action != "list" and not resource_id:
        blockers.append(f"file resource {resource.name!r} requires resource_id for action {action!r}")

    if resource_id and (".." in resource_id or resource_id.startswith("/")):
        blockers.append(
            f"file resource {resource.name!r} resource_id must be a relative document path",
        )

    params = dict(resource.params or {})
    fmt = str(params.get("format") or "json").strip().lower()
    if fmt not in {"json", "text"}:
        blockers.append(f"file resource {resource.name!r} params.format must be json or text")

    if action == "write" and params.get("content") is None and params.get("value") is None:
        blockers.append(
            f"file resource {resource.name!r} action write requires params.content or params.value",
        )

    return blockers


__all__ = ["validate_file_resource", "validate_kv_resource"]