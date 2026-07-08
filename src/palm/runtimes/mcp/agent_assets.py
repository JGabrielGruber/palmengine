"""Resolve portable agent skill files for MCP resources."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

# Keys map to MCP resource suffixes under palm://agent/
SKILL_ASSET_FILES: dict[str, str] = {
    "skill": "SKILL.md",
    "references/agent-guide": "references/agent-guide.md",
    "references/mcp-patterns": "references/mcp-patterns.md",
    "references/session-management": "references/session-management.md",
    "references/common-flows": "references/common-flows.md",
    "references/design-flows": "references/design-flows.md",
    "references/branching-flows": "references/branching-flows.md",
}


def resolve_skill_root(override: str | None) -> Path | None:
    """Return the directory containing ``SKILL.md`` and ``references/``."""
    if override:
        candidate = Path(override)
        if candidate.is_dir() and (candidate / "SKILL.md").is_file():
            return candidate
    bundled = _bundled_skill_root()
    if bundled is not None:
        return bundled
    return _dev_checkout_skill_root()


def read_skill_asset(root: Path, resource_suffix: str) -> str:
    """Read one skill asset by MCP resource suffix (e.g. ``skill``, ``references/agent-guide``)."""
    rel = SKILL_ASSET_FILES.get(resource_suffix)
    if rel is None:
        known = ", ".join(sorted(SKILL_ASSET_FILES))
        raise ValueError(f"unknown agent skill resource: {resource_suffix!r} (known: {known})")
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(f"missing skill asset: {path}")
    return path.read_text(encoding="utf-8")


def _bundled_skill_root() -> Path | None:
    try:
        candidate = resources.files("palm.runtimes.mcp.data").joinpath("skills/palm")
        with resources.as_file(candidate) as path:
            if path.is_dir() and (path / "SKILL.md").is_file():
                return path
    except (FileNotFoundError, ModuleNotFoundError, TypeError, ValueError):
        pass
    return None


def _dev_checkout_skill_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "docs" / "skills" / "palm"
        if candidate.is_dir() and (candidate / "SKILL.md").is_file():
            return candidate
    return None


__all__ = ["SKILL_ASSET_FILES", "read_skill_asset", "resolve_skill_root"]