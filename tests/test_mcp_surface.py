"""MCP surface profiles (0.31.1) — tool registration filters."""

from __future__ import annotations

import asyncio

import pytest

from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.in_process import create_in_process_backend
from palm.runtimes.mcp.server import create_mcp_server
from palm.runtimes.mcp.surface import (
    DEFAULT_SURFACE,
    normalize_surface,
    surface_includes,
    surface_tool_groups,
)


def test_normalize_surface_defaults() -> None:
    assert normalize_surface(None) == DEFAULT_SURFACE
    assert normalize_surface("") == "full"
    assert normalize_surface("ASSIST") == "assist"
    assert normalize_surface("nope") == "full"


def test_surface_includes_assist_only() -> None:
    assert surface_includes("assist", "assist") is True
    assert surface_includes("assist", "flows") is False
    assert surface_includes("assist", "design") is False
    assert surface_includes("core", "system") is True
    assert surface_includes("core", "flows") is False
    assert surface_includes("full", "patterns") is True


def test_from_env_reads_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_SURFACE", "assist")
    cfg = PalmMcpConfig.from_env()
    assert cfg.surface == "assist"


async def _tool_names(surface: str) -> set[str]:
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
        surface=surface,
    )
    backend = create_in_process_backend(config)
    server = create_mcp_server(config, client=backend)
    tools = await server.list_tools()
    return {t.name for t in tools}


def test_assist_surface_registers_only_palm_assist() -> None:
    names = asyncio.run(_tool_names("assist"))
    assert "palm_assist" in names
    assert "palm_flows_session" not in names
    assert "palm_design_publish_flow" not in names
    assert "palm_system_doctor" not in names
    # only the meta tool (name may be prefixed by host later; FastMCP uses bare name)
    assert names == {"palm_assist"} or names == {"palm_assist"} | {
        n for n in names if n.startswith("palm_assist")
    }
    assert all("assist" in n for n in names)


def test_full_surface_has_domain_tools() -> None:
    names = asyncio.run(_tool_names("full"))
    assert "palm_assist" in names
    assert "palm_flows_list" in names or any("flows" in n for n in names)
    assert any("design" in n for n in names)
    assert len(names) > 10


def test_core_surface_has_assist_and_system() -> None:
    names = asyncio.run(_tool_names("core"))
    assert "palm_assist" in names
    assert "palm_system_doctor" in names
    assert "palm_flows_session" not in names
    assert not any(n.startswith("palm_design") for n in names)


def test_assist_surface_smaller_than_full() -> None:
    full = asyncio.run(_tool_names("full"))
    assist = asyncio.run(_tool_names("assist"))
    assert len(assist) < len(full)
    assert len(assist) <= 2
    assert surface_tool_groups("assist") == frozenset({"assist"})
