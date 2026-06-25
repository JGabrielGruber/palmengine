"""Shared version helpers for docs-check and sync-version."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src/palm/__init__.py"


def read_version() -> str:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not read version from pyproject.toml")
    version = match.group(1)

    init = INIT.read_text(encoding="utf-8")
    init_match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    if not init_match:
        raise RuntimeError("Could not read __version__ from src/palm/__init__.py")
    if init_match.group(1) != version:
        raise RuntimeError(
            f"Version mismatch: pyproject.toml={version!r} "
            f"vs __init__.py={init_match.group(1)!r}"
        )
    return version


def write_version(version: str) -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    updated_pyproject, count = re.subn(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{version}"',
        pyproject,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("Could not update version in pyproject.toml")
    PYPROJECT.write_text(updated_pyproject, encoding="utf-8")

    init = INIT.read_text(encoding="utf-8")
    updated_init, count = re.subn(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{version}"',
        init,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Could not update __version__ in src/palm/__init__.py")
    INIT.write_text(updated_init, encoding="utf-8")

    docstring_match = re.search(
        r"(Public API version: ``palm\.__version__`` \(currently )([^)]+)(\)\.)",
        updated_init,
    )
    if docstring_match:
        patched = (
            updated_init[: docstring_match.start(2)]
            + version
            + updated_init[docstring_match.end(2) :]
        )
        INIT.write_text(patched, encoding="utf-8")