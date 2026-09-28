#!/usr/bin/env python3
"""Kernel driver guard (0.72.6).

``palm.system`` does not import ``drivers``. The bundle binds storage and
workload runtimes before ``start``.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_SYSTEM = Path("src/palm/system")


def _driver_import(module: str | None) -> bool:
    if module is None:
        return False
    return module == "drivers" or module.startswith("drivers.")


def _violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [f"{path.as_posix()}: {exc}"]
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _driver_import(alias.name):
                    found.append(f"{path.as_posix()}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and _driver_import(node.module):
            found.append(f"{path.as_posix()}:{node.lineno}: from {node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name != "import_module" or not node.args:
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if _driver_import(arg.value):
                    found.append(f"{path.as_posix()}:{node.lineno}: import_module {arg.value}")
    return found


def main() -> int:
    if not _SYSTEM.is_dir():
        print("palm.system package missing: src/palm/system")
        return 1
    violations: list[str] = []
    for path in sorted(_SYSTEM.rglob("*.py")):
        violations.extend(_violations(path))
    if violations:
        print("Kernel driver import violations:")
        print("\n".join(violations))
        return 1
    print("[OK] palm.system does not import drivers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
