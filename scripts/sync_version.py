#!/usr/bin/env python3
"""Sync package version from pyproject.toml to user-facing documentation surfaces."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from version_utils import ROOT, read_version, write_version  # noqa: E402

SYNC_TARGETS: dict[Path, list[tuple[re.Pattern[str], str]]] = {}


def _register_targets(version: str) -> None:
    SYNC_TARGETS.clear()
    SYNC_TARGETS[ROOT / "README.md"] = [
        (
            re.compile(r"(\*\*Current release:\*\* `)[^`]+(`)"),
            rf"\g<1>{version}\g<2>",
        ),
    ]
    SYNC_TARGETS[ROOT / "STATUS.md"] = [
        (
            re.compile(r"(\*\*Current Version:\*\* `)[^`]+(`)"),
            rf"\g<1>{version}\g<2>",
        ),
    ]
    SYNC_TARGETS[ROOT / "docs/llms.txt"] = [
        (
            re.compile(r"(\*\*Version:\*\* )[0-9.]+"),
            rf"\g<1>{version}",
        ),
    ]
    index = ROOT / "docs/index.html"
    SYNC_TARGETS[index] = [
        (re.compile(r'("version": ")[^"]+(")'), rf'\g<1>{version}\g<2>'),
        (re.compile(r'("softwareVersion": ")[^"]+(")'), rf'\g<1>{version}\g<2>'),
        (re.compile(r"(>v)[0-9.]+( —)"), rf"\g<1>{version}\g<2>"),
    ]


def sync_surfaces(version: str, *, dry_run: bool = False) -> list[str]:
    _register_targets(version)
    changes: list[str] = []
    for path, replacements in SYNC_TARGETS.items():
        text = path.read_text(encoding="utf-8")
        updated = text
        for pattern, repl in replacements:
            updated = pattern.sub(repl, updated)
        if updated != text:
            rel = path.relative_to(ROOT)
            changes.append(str(rel))
            if not dry_run:
                path.write_text(updated, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", dest="new_version", help="Bump pyproject + __init__ then sync")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if sync targets are out of date (no writes)",
    )
    args = parser.parse_args()

    if args.new_version:
        write_version(args.new_version)
        version = args.new_version
    else:
        version = read_version()

    changes = sync_surfaces(version, dry_run=args.check)
    if args.check:
        if changes:
            print("Version sync required for:")
            for item in changes:
                print(f"  - {item}")
            print(f"Run: uv run python scripts/sync_version.py  (version {version})")
            return 1
        print(f"[OK] Sync targets aligned on {version}")
        return 0

    if changes:
        print(f"Synced {version} to:")
        for item in changes:
            print(f"  - {item}")
    else:
        print(f"[OK] Sync targets already on {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())