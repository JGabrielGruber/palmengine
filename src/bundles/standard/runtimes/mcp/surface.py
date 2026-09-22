"""MCP surface profiles — which tool groups register on palm-mcp (0.31.1)."""

from __future__ import annotations

from typing import Final

# Tool registration groups (resources/prompts are orthogonal; see server.py)
TOOL_GROUPS: Final[frozenset[str]] = frozenset(
    {
        "assist",
        "flows",
        "definitions",
        "design",
        "system",
        "providers",
        "patterns",
        "apps",
    }
)

_SURFACE_GROUPS: Final[dict[str, frozenset[str]]] = {
    "full": TOOL_GROUPS,
    # Meta-execute only — host injects ~1 tool instead of ~40
    "assist": frozenset({"assist"}),
    # Assist + system escape hatches (doctor, waiting, jobs)
    "core": frozenset({"assist", "system"}),
    # Placeholder for future experiments (same as full until used)
    "experimental": TOOL_GROUPS,
}

DEFAULT_SURFACE: Final[str] = "full"
VALID_SURFACES: Final[frozenset[str]] = frozenset(_SURFACE_GROUPS)


def normalize_surface(raw: str | None) -> str:
    """Return a valid surface id; unknown values fall back to ``full``."""
    if raw is None or not str(raw).strip():
        return DEFAULT_SURFACE
    key = str(raw).strip().lower()
    if key not in VALID_SURFACES:
        return DEFAULT_SURFACE
    return key


def surface_tool_groups(surface: str | None) -> frozenset[str]:
    """Tool groups enabled for ``surface``."""
    key = normalize_surface(surface)
    return _SURFACE_GROUPS[key]


def surface_includes(surface: str | None, group: str) -> bool:
    """True when ``group`` tools should register for this surface."""
    return group in surface_tool_groups(surface)


__all__ = [
    "DEFAULT_SURFACE",
    "TOOL_GROUPS",
    "VALID_SURFACES",
    "normalize_surface",
    "surface_includes",
    "surface_tool_groups",
]
