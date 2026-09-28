#!/usr/bin/env python3
"""Kernel install guard (0.72.5).

``palm.system`` has no install phase. The only remaining install-key names
are the two keys ``BaseRuntime.start`` refuses.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SYSTEM = Path("src/palm/system")
_PHASE = _SYSTEM / "runtime" / "phase_plugins.py"
_START = _SYSTEM / "runtime" / "base.py"
_FAMILY = '("kits", "patterns", "providers", "runners", "storages", "transforms")'
_GONE = ("system.plugins.ensure", "phase_plugins")
_KEYS = ("plugin_install", "composition_packages")


def main() -> int:
    if not _SYSTEM.is_dir():
        print("palm.system package missing: src/palm/system")
        return 1

    violations: list[str] = []
    if _PHASE.is_file():
        violations.append(f"{_PHASE.as_posix()} still exists")

    for path in sorted(_SYSTEM.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        rel = path.as_posix()
        if _FAMILY in text:
            violations.append(f"{rel}: install family tuple")
        for word in _GONE:
            if word in text:
                violations.append(f"{rel}: {word}")
        if path != _START:
            for word in _KEYS:
                if word in text:
                    violations.append(f"{rel}: {word}")

    if _START.is_file():
        start = _START.read_text(encoding="utf-8")
        for word in _KEYS:
            count = start.count(word)
            if count != 1:
                violations.append(f"{_START.as_posix()}: {word} appears {count} times")
    else:
        violations.append(f"{_START.as_posix()} missing")

    if violations:
        print("Kernel install violations:")
        print("\n".join(violations))
        return 1

    print("[OK] palm.system has no install phase")
    return 0


if __name__ == "__main__":
    sys.exit(main())
