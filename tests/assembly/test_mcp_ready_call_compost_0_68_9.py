"""0.68.9 — Pattern MCP second ready() call composted."""

from __future__ import annotations

import inspect

from palm.common.patterns.app import PatternApp
from palm.common.providers.app import ProviderApp
from bundles.standard.runtimes.mcp.contributors import register_pattern_mcp_tools


def test_mcp_registrar_does_not_call_ready() -> None:
    src = inspect.getsource(register_pattern_mcp_tools)
    assert "app.ready()" not in src
    assert "autoload_patterns" in src
    assert "iter_mcp_contributors" in src


def test_pattern_and_provider_register_still_call_ready() -> None:
    assert "self.ready()" in inspect.getsource(PatternApp.register)
    assert "self.ready()" in inspect.getsource(ProviderApp.register)
