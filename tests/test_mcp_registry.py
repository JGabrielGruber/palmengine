"""Tests for pattern MCP contributor registry."""

from __future__ import annotations

from palm.common.patterns._registry import (
    McpContributor,
    clear_mcp_contributors,
    get_mcp_contributor,
    iter_mcp_contributors,
    register_mcp_contributor,
)


def test_register_and_iterate_mcp_contributors() -> None:
    from palm.common.patterns._registry import iter_mcp_contributors as _before

    saved = list(_before())
    clear_mcp_contributors()
    try:
        seen: list[str] = []

        def _register(_mcp: object, _client: object) -> None:
            seen.append("wizard")

        register_mcp_contributor(McpContributor(pattern_name="wizard", register=_register))
        contributors = iter_mcp_contributors()
        assert len(contributors) == 1
        assert contributors[0].pattern_name == "wizard"
        assert get_mcp_contributor("wizard") is contributors[0]
        contributors[0].register(object(), object())
        assert seen == ["wizard"]
    finally:
        clear_mcp_contributors()
        for contributor in saved:
            register_mcp_contributor(contributor)
