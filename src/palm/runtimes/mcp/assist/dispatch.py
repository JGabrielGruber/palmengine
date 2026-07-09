"""Parametric operator dispatch — public re-exports (0.33.3 modular split).

Implementation lives in::

    normalize.py   — path/alias/params normalization
    operator.py    — in-process service dispatch
    shape/         — assistant/powertool result shaping
    rest_map.py    — REST path mapping for proxy mode
"""

from __future__ import annotations

from typing import Any

from palm.runtimes.mcp.assist.normalize import (
    normalize_assist_dispatch_args,
    resolve_dispatch_path,
)
from palm.runtimes.mcp.assist.operator import dispatch_operator_path
from palm.runtimes.mcp.assist.rest_map import map_dispatch_to_rest
from palm.runtimes.mcp.assist.routes_catalog import build_assist_routes_catalog
from palm.runtimes.mcp.assist.shape.result import (
    compact_dispatch_result,
    resolve_dispatch_format,
    shape_dispatch_result,
)


def assist_routes_payload() -> dict[str, Any]:
    return build_assist_routes_catalog()


__all__ = [
    "assist_routes_payload",
    "compact_dispatch_result",
    "dispatch_operator_path",
    "map_dispatch_to_rest",
    "normalize_assist_dispatch_args",
    "resolve_dispatch_format",
    "resolve_dispatch_path",
    "shape_dispatch_result",
]
