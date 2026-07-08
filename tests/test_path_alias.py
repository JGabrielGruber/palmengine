"""Tests for shared MCP path alias resolution."""

from __future__ import annotations

import pytest

from palm.common.operator.path_alias import resolve_path_alias
from palm.common.operator.path_match import match_command_path
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


def test_match_command_path_is_inverse_of_alias_resolution() -> None:
    pattern = ("design", "proposals", "{proposal_id}", "commit")
    resolved = resolve_path_alias("design/commit", pattern, params={"proposal_id": "prop-abc"})
    assert resolved is not None
    capture = match_command_path(resolved, pattern)
    assert capture == {"proposal_id": "prop-abc"}


def test_design_registry_uses_shared_resolver() -> None:
    path = resolve_design_mcp_alias("design/validate", params={"proposal_id": "prop-xyz"})
    assert path == ("design", "proposals", "prop-xyz", "validate")