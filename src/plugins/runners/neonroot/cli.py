"""Detect and probe the host NeonRoot CLI (optional dependency)."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NeonrootProbe:
    """Snapshot of NeonRoot availability on this host."""

    available: bool
    path: str | None = None
    version: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "path": self.path,
            "version": self.version,
            "error": self.error,
        }


def find_neonroot_binary() -> str | None:
    """Return absolute path to ``neonroot`` if on PATH."""
    return shutil.which("neonroot")


def probe_neonroot(*, timeout: float = 5.0) -> NeonrootProbe:
    """Locate ``neonroot`` and optionally read ``--version``."""
    path = find_neonroot_binary()
    if not path:
        return NeonrootProbe(
            available=False,
            error="neonroot not found on PATH (optional — install NeonRoot for hermetic runners)",
        )
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return NeonrootProbe(available=False, path=path, error=str(exc))

    out = (proc.stdout or proc.stderr or "").strip()
    version = out.splitlines()[0].strip() if out else None
    if proc.returncode != 0 and not version:
        return NeonrootProbe(
            available=False,
            path=path,
            error=f"neonroot --version exited {proc.returncode}",
        )
    return NeonrootProbe(available=True, path=path, version=version)


__all__ = ["NeonrootProbe", "find_neonroot_binary", "probe_neonroot"]
