"""Tests for shared MCP path alias resolution."""

from __future__ import annotations

import pytest

from palm.common.operator.path_alias import resolve_path_alias
from palm.services.design.registry import resolve_design_mcp_alias


def test_resolve_path_alias_substitutes_params() -> None:
    path = resolve_path_alias(
        "demo/commit",
        ("design", "proposals", "{proposal_id}", "commit"),
        params={"proposal_id": "prop-abc"},
    )
    assert path == ("design", "proposals", "prop-abc", "commit")


def test_resolve_path_alias_requires_params() -> None:
    with pytest.raises(ValueError, match="requires param"):
        resolve_path_alias(
            "demo/commit",
            ("design", "proposals", "{proposal_id}", "commit"),
        )


def test_design_registry_uses_shared_resolver() -> None:
    path = resolve_design_mcp_alias("design/validate", params={"proposal_id": "prop-xyz"})
    assert path == ("design", "proposals", "prop-xyz", "validate")