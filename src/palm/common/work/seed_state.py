"""Resolve inbound ``work.seed_state`` paths into blackboard seed dicts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.common.transforms.rules._jsonpath import _MISSING, jsonpath_get


def resolve_seed_state(
    mapping: Mapping[str, str],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Map ``target_key -> path`` against ``payload`` (dot or ``$.`` paths)."""
    if not mapping:
        return {}
    root = dict(payload)
    out: dict[str, Any] = {}
    for target_key, path in mapping.items():
        if not target_key or not path:
            continue
        normalized = str(path).strip()
        if normalized.startswith("$."):
            normalized = normalized[2:]
        elif normalized.startswith("$"):
            normalized = normalized[1:].lstrip(".")
        try:
            value = jsonpath_get(root, normalized, default=_MISSING)
        except Exception:
            continue
        if value is _MISSING:
            continue
        out[str(target_key)] = value
    return out


__all__ = ["resolve_seed_state"]