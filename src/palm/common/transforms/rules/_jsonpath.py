"""Minimal dot-path navigation for dict/list payloads (no external deps)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from palm.core.exceptions import TransformApplicationError

_MISSING = object()


def jsonpath_get(
    data: Any,
    path: str,
    *,
    default: Any = _MISSING,
) -> Any:
    """Read a value at a dot-separated path (e.g. ``user.name``, ``items.0.id``)."""
    if not path:
        raise TransformApplicationError("jsonpath requires a non-empty path")
    current = data
    for segment in path.split("."):
        if current is None:
            if default is not _MISSING:
                return default
            raise TransformApplicationError(f"jsonpath {path!r} reached null at {segment!r}")
        if isinstance(current, dict):
            if segment not in current:
                if default is not _MISSING:
                    return default
                raise TransformApplicationError(
                    f"jsonpath {path!r} missing key {segment!r}",
                )
            current = current[segment]
            continue
        if isinstance(current, list):
            try:
                index = int(segment)
            except ValueError as exc:
                raise TransformApplicationError(
                    f"jsonpath {path!r} expected list index, got {segment!r}",
                ) from exc
            if index < 0 or index >= len(current):
                if default is not _MISSING:
                    return default
                raise TransformApplicationError(
                    f"jsonpath {path!r} index {index} out of range",
                )
            current = current[index]
            continue
        if default is not _MISSING:
            return default
        raise TransformApplicationError(
            f"jsonpath {path!r} cannot traverse {type(current).__name__} at {segment!r}",
        )
    return current


def jsonpath_set(data: Any, path: str, value: Any) -> Any:
    """Return a copy of ``data`` with ``value`` written at ``path``."""
    if not path:
        raise TransformApplicationError("jsonpath requires a non-empty path")
    if not isinstance(data, dict):
        raise TransformApplicationError(
            f"jsonpath_set requires a mapping root, got {type(data).__name__}",
        )
    root = deepcopy(data)
    segments = path.split(".")
    current: Any = root
    for segment in segments[:-1]:
        if not isinstance(current, dict):
            raise TransformApplicationError(
                f"jsonpath_set cannot traverse {type(current).__name__} at {segment!r}",
            )
        next_value = current.get(segment)
        if next_value is None:
            next_value = {}
            current[segment] = next_value
        elif not isinstance(next_value, dict):
            raise TransformApplicationError(
                f"jsonpath_set intermediate {segment!r} is not a mapping",
            )
        current = next_value
    leaf = segments[-1]
    if not isinstance(current, dict):
        raise TransformApplicationError(
            f"jsonpath_set cannot write into {type(current).__name__}",
        )
    current[leaf] = value
    return root