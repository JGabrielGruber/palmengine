"""Architectural boundary tests for provider packages."""

from __future__ import annotations

import ast
from pathlib import Path


_ALLOWED_COMMON_PROVIDER_MODULES = frozenset({"palm.providers._registry"})


def test_common_has_no_provider_imports() -> None:
    """``palm.common`` must not import provider app internals (bindings, flow, etc.)."""
    common_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "common"
    repo_root = common_root.parents[1]
    violations: list[str] = []

    for path in sorted(common_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if (
                    node.module.startswith("palm.providers.")
                    and node.module not in _ALLOWED_COMMON_PROVIDER_MODULES
                ):
                    violations.append(
                        f"{path.relative_to(repo_root)}: from {node.module}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if (
                        alias.name.startswith("palm.providers.")
                        and alias.name not in _ALLOWED_COMMON_PROVIDER_MODULES
                    ):
                        violations.append(
                            f"{path.relative_to(repo_root)}: import {alias.name}"
                        )

    assert not violations, "provider imports found in palm.common:\n" + "\n".join(violations)


def test_patterns_have_no_provider_internals() -> None:
    """``palm.patterns`` must not import palm provider bindings or flow modules."""
    patterns_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "patterns"
    repo_root = patterns_root.parents[1]
    banned_fragments = (
        "palm.providers.palm.bindings",
        "palm.providers.palm.flow",
    )
    violations: list[str] = []

    for path in sorted(patterns_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if any(fragment in node.module for fragment in banned_fragments):
                    violations.append(
                        f"{path.relative_to(repo_root)}: from {node.module}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(fragment in alias.name for fragment in banned_fragments):
                        violations.append(
                            f"{path.relative_to(repo_root)}: import {alias.name}"
                        )

    assert not violations, "palm provider internals found in palm.patterns:\n" + "\n".join(
        violations
    )