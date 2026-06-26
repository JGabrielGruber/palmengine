"""Configuration for the Palm MCP stdio adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
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
        llms_path = Path(llms_override) if llms_override else _default_llms_path()
        return cls(base_url=base_url, subject=subject, llms_txt_path=llms_path)


def _default_llms_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "docs" / "llms.txt"
        if candidate.is_file():
            return candidate
    return None


__all__ = ["PalmMcpConfig"]