"""Operator view format registry — thin dispatch to registered builders."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from palm.common.operator.compact import compact_job_inspect, compact_wizard_inspect

ViewBuilderFn = Callable[..., dict[str, Any]]

_FORMAT_ALIASES = {"compact": "powertool"}

_lock = threading.RLock()
_builders: dict[str, ViewBuilderFn] = {}


@dataclass
class OperatorViewContext:
    """Context passed to operator view builders."""

    session_id: str | None = None
    flow_id: str | None = None
    scenario_id: str | None = None
    invoke_tree: dict[str, Any] | None = None
    handoff_ready: bool = False
    path: list[str] = field(default_factory=list)


def normalize_view_format(format: str) -> str:
    """Map deprecated aliases to canonical format names."""
    return _FORMAT_ALIASES.get(format, format)


def register_operator_view_builder(format: str, fn: ViewBuilderFn) -> None:
    """Register a builder for ``format`` (e.g. ``powertool``, ``assistant``)."""
    key = normalize_view_format(format)
    with _lock:
        _builders[key] = fn


def allowed_view_formats() -> frozenset[str]:
    """Return registered formats plus built-in ``verbose``."""
    with _lock:
        return frozenset(_builders) | {"verbose"}


def build_operator_view(
    format: str,
    *,
    flat_view: dict[str, Any],
    context: OperatorViewContext | None = None,
) -> dict[str, Any]:
    """Dispatch ``flat_view`` to the registered builder for ``format``."""
    key = normalize_view_format(format)
    if key == "verbose":
        return dict(flat_view)

    with _lock:
        builder = _builders.get(key)
        allowed = sorted(allowed_view_formats())

    if builder is None:
        raise ValueError(f"unknown operator view format: {format!r} (allowed: {allowed})")

    ctx = context or OperatorViewContext()
    return builder(flat_view, context=ctx)


def clear_operator_view_builders() -> None:
    """Reset registry to built-in builders (primarily for tests)."""
    with _lock:
        _builders.clear()
        _register_builtins()


def _is_job_context(flat_view: dict[str, Any]) -> bool:
    return "job_id" in flat_view and ("pattern" in flat_view or "instance" in flat_view)


def _build_powertool_view(
    flat_view: dict[str, Any],
    *,
    context: OperatorViewContext,
) -> dict[str, Any]:
    flat = dict(flat_view)
    if context.session_id:
        flat.setdefault("session_id", context.session_id)
        if not flat.get("instance_id"):
            flat["instance_id"] = context.session_id
    if context.flow_id:
        flat.setdefault("flow_name", context.flow_id)
    if _is_job_context(flat):
        return compact_job_inspect(flat, format="compact")
    return compact_wizard_inspect(flat, format="compact")


def _register_builtins() -> None:
    _builders["powertool"] = _build_powertool_view


_register_builtins()

__all__ = [
    "OperatorViewContext",
    "allowed_view_formats",
    "build_operator_view",
    "clear_operator_view_builders",
    "normalize_view_format",
    "register_operator_view_builder",
]