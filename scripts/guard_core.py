#!/usr/bin/env python3
"""Core purity guard — no imports from outer layers inside palm.core."""

from __future__ import annotations

import sys
from pathlib import Path

FORBIDDEN = (
    "patterns",
    "providers",
    "storages",
    "runtimes",
    "definitions",
    "common",
    "executions",
    "utils",
)
FORBIDDEN_TEST_ARTIFACTS = ("TestMode", "TestRunner", "StubInteractiveLeaf")


def main() -> int:
    core = Path("src/palm/core")
    violations: list[str] = []

    for py in core.rglob("*.py"):
        if py.name.startswith("test_"):
            violations.append(f"test module in core: {py}")
        text = py.read_text(encoding="utf-8")
        for name in FORBIDDEN_TEST_ARTIFACTS:
            if f"class {name}" in text:
                violations.append(f"{py}: forbidden test class {name}")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("from palm.") and not stripped.startswith("import palm."):
                continue
            for pkg in FORBIDDEN:
                if f"palm.{pkg}" in stripped:
                    violations.append(f"{py}: {stripped}")

    if violations:
        print("Core purity violations:")
        print("\n".join(violations))
        return 1

    print("[OK] Core architecture rules respected")
    return 0


if __name__ == "__main__":
    sys.exit(main())