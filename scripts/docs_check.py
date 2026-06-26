#!/usr/bin/env python3
"""Documentation freshness guard — version and surface consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from version_utils import PYPROJECT, INIT, read_version  # noqa: E402

STALE_ARCHITECTURE_PATTERNS = (
    (re.compile(r"patterns/wizard/handler\.py"), "use patterns/wizard/bindings/compensation/handler.py"),
    (
        re.compile(r"\bwizard_step_slug\b"),
        "use current_step_slug (legacy JSON compat only in readers)",
    ),
    (
        re.compile(r"pattern\.py[`'\"]? \+ [`'\"]?builder\.py"),
        "use bindings/definitions/builder.py — see docs/PATTERN-APPS.md",
    ),
    (
        re.compile(r"providers/palm/(coordinator|params|payload|target|remote|wiring|recursion)\.py"),
        "use bindings/ + flow/ layout — see docs/PROVIDER-APPS.md",
    ),
)

STALE_ARCHITECTURE_SCAN_PATHS = (
    ROOT / "README.md",
    ROOT / "STATUS.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "DEVELOPMENT.md",
    ROOT / "AGENTS.md",
    ROOT / "docs/llms.txt",
    ROOT / "docs/PATTERN-APPS.md",
    ROOT / "docs/PROVIDER-APPS.md",
)

STALE_VERSION_PATTERNS = (
    re.compile(r"\b0\.10\.9\b"),
    re.compile(r"\bv0\.10\.9\b"),
    re.compile(r"\b0\.9\.7\b"),
    re.compile(r"\bv0\.9\.7\b"),
    re.compile(r'"softwareVersion":\s*"0\.9'),
    re.compile(r'"version":\s*"0\.9'),
)

VERSION_SOURCES = (PYPROJECT, INIT)

SYNC_SURFACE_FILES = (
    ROOT / "README.md",
    ROOT / "STATUS.md",
    ROOT / "docs/index.html",
    ROOT / "docs/llms.txt",
)

BUNDLED_LLMS_TXT = ROOT / "src/palm/runtimes/mcp/data/llms.txt"


def check_version_sources(version: str, errors: list[str]) -> None:
    for path in VERSION_SOURCES:
        text = path.read_text(encoding="utf-8")
        if version not in text:
            errors.append(f"{path.relative_to(ROOT)}: expected version {version!r}")


def check_sync_surfaces(version: str, errors: list[str]) -> None:
    for path in SYNC_SURFACE_FILES:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if version not in text:
            errors.append(f"{rel}: missing current version {version!r} (run sync-version)")

    index_html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    for field in ("version", "softwareVersion"):
        pattern = re.compile(rf'"{field}":\s*"{re.escape(version)}"')
        if not pattern.search(index_html):
            errors.append(f"docs/index.html: JSON-LD {field!r} not set to {version!r}")

    hero_pattern = re.compile(rf"\bv{re.escape(version)}\b")
    if not hero_pattern.search(index_html):
        errors.append(f"docs/index.html: hero badge missing v{version}")


def check_stale_architecture_refs(errors: list[str]) -> None:
    """Flag outdated pattern layout references on active documentation surfaces."""
    for path in STALE_ARCHITECTURE_SCAN_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for pattern, hint in STALE_ARCHITECTURE_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel}: stale architecture reference ({hint})")


def check_bundled_llms_txt(errors: list[str]) -> None:
    source = ROOT / "docs/llms.txt"
    if not source.is_file():
        errors.append("docs/llms.txt: missing source agent guide")
        return
    if not BUNDLED_LLMS_TXT.is_file():
        errors.append(
            "src/palm/runtimes/mcp/data/llms.txt: missing bundled MCP agent guide"
        )
        return
    if source.read_text(encoding="utf-8") != BUNDLED_LLMS_TXT.read_text(encoding="utf-8"):
        errors.append(
            "src/palm/runtimes/mcp/data/llms.txt: out of sync with docs/llms.txt "
            "(copy docs/llms.txt into the MCP data package)"
        )


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
    check_sync_surfaces(version, errors)
    check_stale_architecture_refs(errors)
    check_bundled_llms_txt(errors)
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