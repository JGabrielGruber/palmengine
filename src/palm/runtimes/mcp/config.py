"""Configuration for the Palm MCP stdio adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from palm.runtimes.mcp.agent_assets import resolve_skill_root


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PalmMcpConfig:
    """Environment-driven settings for MCP operator backends."""

    base_url: str
    subject: str
    llms_txt_path: Path | None = None
    skill_root: Path | None = None
    in_process: bool = False

    @classmethod
    def from_env(cls) -> PalmMcpConfig:
        base_url = os.environ.get("PALM_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
        subject = os.environ.get("PALM_SUBJECT", "dev")
        llms_override = os.environ.get("PALM_LLMS_TXT", "").strip()
        skill_override = os.environ.get("PALM_SKILL_DIR", "").strip()
        llms_path = _resolve_llms_path(llms_override or None)
        skill_path = resolve_skill_root(skill_override or None)
        in_process = _env_flag("PALM_MCP_IN_PROCESS")
        return cls(
            base_url=base_url,
            subject=subject,
            llms_txt_path=llms_path,
            skill_root=skill_path,
            in_process=in_process,
        )


def _resolve_llms_path(override: str | None) -> Path | None:
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate
    bundled = _bundled_agent_guide_path()
    if bundled is not None:
        return bundled
    return _dev_checkout_agent_guide_path()


def _bundled_agent_guide_path() -> Path | None:
    for name in ("mcp.txt", "llms.txt"):
        try:
            candidate = resources.files("palm.runtimes.mcp.data").joinpath(name)
            with resources.as_file(candidate) as path:
                if path.is_file():
                    return path
        except (FileNotFoundError, ModuleNotFoundError, TypeError, ValueError):
            continue
    return None


def _dev_checkout_agent_guide_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        for name in ("mcp.txt", "llms.txt"):
            candidate = parent / "docs" / name
            if candidate.is_file():
                return candidate
    return None


__all__ = ["PalmMcpConfig"]
