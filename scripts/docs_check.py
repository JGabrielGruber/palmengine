#!/usr/bin/env python3
"""Documentation freshness guard — version and surface consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STALE_VERSION_PATTERNS = (
    re.compile(r"\b0\.9\.7\b"),
    re.compile(r"\bv0\.9\.7\b"),
    re.compile(r'"softwareVersion":\s*"0\.9'),
    re.compile(r'"version":\s*"0\.9'),
)

VERSION_SOURCES = (
    ROOT / "pyproject.toml",
    ROOT / "src/palm/__init__.py",
)

SURFACE_FILES = (
    ROOT / "README.md",
    ROOT / "STATUS.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "DEVELOPMENT.md",
    ROOT / "docs/index.html",
    ROOT / "docs/llms.txt",
    ROOT / "CHANGELOG.md",
)


def read_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not read version from pyproject.toml")
    version = match.group(1)

    init = (ROOT / "src/palm/__init__.py").read_text(encoding="utf-8")
    init_match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    if not init_match:
        raise RuntimeError("Could not read __version__ from src/palm/__init__.py")
    if init_match.group(1) != version:
        raise RuntimeError(
            f"Version mismatch: pyproject.toml={version!r} "
            f"vs __init__.py={init_match.group(1)!r}"
        )
    return version


def check_version_sources(version: str, errors: list[str]) -> None:
    for path in VERSION_SOURCES:
        text = path.read_text(encoding="utf-8")
        if version not in text:
            errors.append(f"{path.relative_to(ROOT)}: expected version {version!r}")


def check_surfaces(version: str, errors: list[str]) -> None:
    for path in SURFACE_FILES:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if version not in text:
            errors.append(f"{rel}: missing current version {version!r}")

    index_html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    for field in ("version", "softwareVersion"):
        pattern = re.compile(rf'"{field}":\s*"{re.escape(version)}"')
        if not pattern.search(index_html):
            errors.append(f"docs/index.html: JSON-LD {field!r} not set to {version!r}")

    hero_pattern = re.compile(rf"\bv{re.escape(version)}\b")
    if not hero_pattern.search(index_html):
        errors.append(f"docs/index.html: hero badge missing v{version}")


def check_stale_versions(errors: list[str]) -> None:
    """Flag outdated version stamps on active public surfaces (not changelogs/migrations)."""
    scan_paths = [
        ROOT / "docs/index.html",
        ROOT / "docs/llms.txt",
        ROOT / "README.md",
        ROOT / "STATUS.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "DEVELOPMENT.md",
        ROOT / "AGENTS.md",
    ]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in STALE_VERSION_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"{path.relative_to(ROOT)}: stale version reference ({pattern.pattern})"
                )
                break


def main() -> int:
    errors: list[str] = []
    try:
        version = read_version()
    except RuntimeError as exc:
        print(f"docs-check failed: {exc}")
        return 1

    check_version_sources(version, errors)
    check_surfaces(version, errors)
    check_stale_versions(errors)

    if errors:
        print("Documentation consistency violations:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(f"[OK] Documentation surfaces aligned on {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())