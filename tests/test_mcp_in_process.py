"""Tests for in-process MCP backend (``PALM_MCP_IN_PROCESS=1``, no HTTP round-trip).

REST proxy mode (``PalmRestClient`` + ``PALM_BASE_URL``) is tested in ``tests/test_mcp_tools.py``.
"""

from __future__ import annotations

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.in_process import (  # noqa: E402
    PalmInProcessBackend,
    create_in_process_backend,
    shutdown_in_process_runtime,
)
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402
from palm.runtimes.server.factory import build_server_context  # noqa: E402


@pytest.fixture
def server_ctx():
    shutdown_in_process_runtime()
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    ctx = build_server_context(rt)
    yield ctx
    rt.stop()
    shutdown_in_process_runtime()


def test_in_process_backend_inspect_and_doctor(server_ctx) -> None:
    backend = PalmInProcessBackend(server_ctx)
    doctor = backend.get_doctor()
    assert "patterns" in doctor or "runtime" in doctor
    assert backend.get_health()["mode"] == "in_process"


def test_in_process_backend_submit_and_inspect_wizard(server_ctx) -> None:
    backend = PalmInProcessBackend(server_ctx)
    submitted = backend.submit_wizard({"wizard": {"name": "onboard", "steps": 2}})
    instance_id = submitted["instance_id"]
    view = backend.get_wizard(instance_id)
    assert view["instance_id"] == instance_id
    assert view.get("flow_name") == "onboard" or view.get("status")


@pytest.mark.asyncio
async def test_mcp_tools_use_in_process_backend(server_ctx) -> None:
    backend = PalmInProcessBackend(server_ctx)
    submitted = backend.submit_wizard({"wizard": {"name": "onboard", "steps": 2}})
    instance_id = submitted["instance_id"]

    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        doctor = await client.call_tool("palm_doctor", {})
        assert doctor.data

        result = await client.call_tool(
            "palm_inspect_instance",
            {"instance_id": instance_id, "format": "compact"},
        )
    payload = result.data
    assert payload["instance_id"] == instance_id


def test_create_in_process_backend_bootstraps_runtime() -> None:
    shutdown_in_process_runtime()
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    backend = create_in_process_backend(config)
    try:
        health = backend.get_health()
        assert health["status"] == "ok"
        assert health["mode"] == "in_process"
    finally:
        shutdown_in_process_runtime()


def test_config_reads_in_process_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_IN_PROCESS", "1")
    config = PalmMcpConfig.from_env()
    assert config.in_process is True
