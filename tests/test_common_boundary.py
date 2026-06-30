"""Architectural boundary tests for ``palm.common``."""

from __future__ import annotations

import ast
from pathlib import Path


def test_common_has_no_wizard_imports() -> None:
    """``palm.common`` must not import wizard pattern internals directly."""
    common_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "common"
    violations: list[str] = []

    for path in sorted(common_root.rglob("*.py")):
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


def test_common_has_no_wizard_named_modules() -> None:
    """``palm.common`` must not ship wizard-prefixed modules."""
    common_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "common"
    offenders = sorted(
        path.relative_to(common_root.parents[1]) for path in common_root.rglob("wizard*.py")
    )
    assert not offenders, "wizard-prefixed modules in palm.common:\n" + "\n".join(
        str(path) for path in offenders
    )


def test_common_has_no_wizard_identifiers() -> None:
    """``palm.common`` must not define wizard-specific CQRS or read-model symbols."""
    common_root = Path(__file__).resolve().parents[1] / "src" / "palm" / "common"
    banned = {
        "SubmitWizardCommand",
        "ProvideWizardInputCommand",
        "RequestWizardBacktrackCommand",
        "GetWizardProgressQuery",
        "GetWizardStatusQuery",
        "ListWizardProgressQuery",
        "WizardProgressProjection",
        "WizardProgressReadModel",
        "build_wizard_view",
    }
    violations: list[str] = []

    for path in sorted(common_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in banned:
                violations.append(f"{path.name}: class {node.name}")
            elif isinstance(node, ast.FunctionDef) and node.name in banned:
                violations.append(f"{path.name}: def {node.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in banned:
                        violations.append(f"{path.name}: assign {target.id}")

    assert not violations, "wizard identifiers found in palm.common:\n" + "\n".join(violations)
