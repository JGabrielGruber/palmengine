"""Architectural boundary tests for ``palm.common``."""

from __future__ import annotations

import ast
from pathlib import Path


_WIZARD_BRIDGE_ALLOWLIST = {
    "palm/common/wizard_runtime.py",
}


def test_common_has_no_wizard_imports() -> None:
    """``palm.common`` must not import wizard pattern internals directly."""
    common_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "common"
    repo_root = common_root.parents[1]
    violations: list[str] = []

    for path in sorted(common_root.rglob("*.py")):
        rel = str(path.relative_to(repo_root))
        if rel in _WIZARD_BRIDGE_ALLOWLIST:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "patterns.wizard" in node.module or node.module == "palm.patterns.wizard":
                    violations.append(
                        f"{path.relative_to(common_root.parents[1])}: from {node.module}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "patterns.wizard" in alias.name:
                        violations.append(
                            f"{path.relative_to(common_root.parents[1])}: import {alias.name}"
                        )

    assert not violations, "wizard imports found in palm.common:\n" + "\n".join(violations)
