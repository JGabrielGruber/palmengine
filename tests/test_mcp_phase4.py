"""Phase 4 MCP tests — debug and lifecycle tools."""

from __future__ import annotations

from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _Phase4FakeClient:
    def get_doctor(self) -> dict[str, Any]:
        return {"status": "ok", "registries": {"patterns": ["wizard"]}}

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        return {"job_id": job_id, "cancelled": True, "status": "CANCELLED"}

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        return {
            "job_id": job_id,
            "recent_events": [{"type": "wizard.step.completed", "slug": "name"}],
        }

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> dict[str, Any]:
        if snapshot_id == "0":
            return {"state_snapshot": {"name": "Ada"}}
        return {"state_snapshot": {"name": "Bob"}}

    def get_flow(self, flow_id: str, *, verbose: bool = False) -> dict[str, Any]:
        return {
            "name": flow_id,
            "pattern": "wizard",
            "options": {"steps": [{"slug": "name", "field_type": "text"}]},
        }

    def validate_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"valid": True, "pattern": "wizard", "step_slugs": ["name"]}

    def prepare_plans(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"plans": [{"plan_id": "plan-1", "kind": "process"}]}

    def submit_plans(self, plan_ids: list[str]) -> dict[str, Any]:
        return {"jobs": [{"job_id": "job-1", "status": "RUNNING"}]}

    def get_process(self, process_id: str) -> dict[str, Any]:
        if process_id == "catalog":
            return {
                "name": "catalog",
                "flows": [{}, {}],
                "metadata": {"entry_flow": "main-menu"},
            }
        return {"name": process_id, "flows": [{}], "metadata": {}}

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        return {"jobs": []}

    def get_health(self) -> dict[str, Any]:
        return {"status": "ok"}


@pytest.fixture
def phase4_server():
    fake = _Phase4FakeClient()
    server = create_mcp_server(
        PalmMcpConfig(base_url="http://127.0.0.1:8080", subject="dev", llms_txt_path=None),
        client=fake,
    )
    return server, fake


@pytest.mark.asyncio
async def test_palm_doctor_tool(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool("palm_doctor", {})
    assert result.data["status"] == "ok"


@pytest.mark.asyncio
async def test_palm_cancel_job_tool(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool("palm_cancel_job", {"job_id": "job-9"})
    assert result.data["cancelled"] is True


@pytest.mark.asyncio
async def test_palm_trace_events_tool(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool("palm_trace_events", {"job_id": "job-9"})
    assert result.data["count"] == 1


@pytest.mark.asyncio
async def test_palm_diff_snapshots_tool(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_diff_snapshots",
            {"instance_id": "inst-1", "from_snapshot": "0", "to_snapshot": "1"},
        )
    assert result.data["change_count"] == 1


@pytest.mark.asyncio
async def test_palm_submit_process_tool(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_submit_process",
            {"process_name": "pipeline"},
        )
    assert result.data["jobs"][0]["job_id"] == "job-1"


@pytest.mark.asyncio
async def test_palm_submit_process_rejects_interactive_catalog(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        with pytest.raises(Exception, match="interactive catalog"):
            await client.call_tool(
                "palm_submit_process",
                {"process_name": "catalog"},
            )


@pytest.mark.asyncio
async def test_palm_fetch_job_uses_job_context(phase4_server) -> None:
    server, _ = phase4_server
    async with Client(server) as client:
        result = await client.call_tool("palm_fetch_job", {"job_id": "job-9"})
    assert result.data["job_id"] == "job-9"
    assert result.data["recent_events"][0]["type"] == "wizard.step.completed"