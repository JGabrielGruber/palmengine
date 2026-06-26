"""Configuration for the Palm MCP stdio adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class PalmMcpConfig:
    """Environment-driven settings for REST proxying."""

    base_url: str
    subject: str
    llms_txt_path: Path | None

    @classmethod
    def from_env(cls) -> PalmMcpConfig:
        base_url = os.environ.get("PALM_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
        subject = os.environ.get("PALM_SUBJECT", "dev")
        llms_override = os.environ.get("PALM_LLMS_TXT", "").strip()
        llms_path = _resolve_llms_path(llms_override or None)
        return cls(base_url=base_url, subject=subject, llms_txt_path=llms_path)


def _resolve_llms_path(override: str | None) -> Path | None:
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate
    bundled = _bundled_llms_path()
    if bundled is not None:
        return bundled
    return _dev_checkout_llms_path()


def _bundled_llms_path() -> Path | None:
    try:
        candidate = resources.files("palm.runtimes.mcp.data").joinpath("llms.txt")
        with resources.as_file(candidate) as path:
            if path.is_file():
                return path
    except (FileNotFoundError, ModuleNotFoundError, TypeError, ValueError):
        pass
    return None


def _dev_checkout_llms_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "docs" / "llms.txt"
        if candidate.is_file():
            return candidate
    return None


__all__ = ["PalmMcpConfig"]