"""Ensure transform package stays inside palm.core."""

from __future__ import annotations

import ast
from pathlib import Path


def test_transform_package_has_no_external_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "palm" / "core" / "transform"
    violations: list[str] = []

    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("palm.") and not node.module.startswith("palm.core"):
                    violations.append(f"{path.name}: from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("palm.") and not alias.name.startswith("palm.core"):
                        violations.append(f"{path.name}: import {alias.name}")

    assert not violations, "external imports in core/transform:\n" + "\n".join(violations)
