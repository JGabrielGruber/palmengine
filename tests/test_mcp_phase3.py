"""Phase 3 MCP tests — pattern tools and prompts."""

from __future__ import annotations

from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _Phase3FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._collection_phase = "menu"

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        self.calls.append(("get_wizard", instance_id))
        return {
            "instance_id": instance_id,
            "job_id": "job-1",
            "flow_name": "todo_builder",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "items",
            "prompt": {
                "step": "items",
                "step_kind": "collection",
                "collection_phase": self._collection_phase,
                "choices": ["Continue to summary"],
            },
            "answers": {},
        }

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        self.calls.append(("provide_wizard_input", instance_id, value))
        if value == "Add a new item":
            self._collection_phase = "field"
        elif self._collection_phase == "field":
            self._collection_phase = "menu"
        view = self.get_wizard(instance_id)
        return view

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        self.calls.append(("get_job_context", job_id))
        if job_id == "parallel-job":
            return {
                "job_id": job_id,
                "status": "RUNNING",
                "pattern": {
                    "pattern": "parallel",
                    "active_branch": "alpha",
                    "branch_progress": "1/2",
                    "branches": [
                        {"slug": "alpha", "completed": False, "active": True, "step": "name"},
                        {"slug": "beta", "completed": True, "active": False, "step": None},
                    ],
                    "merged": {},
                },
                "instance": {"instance_id": "inst-par"},
            }
        return {
            "job_id": job_id,
            "metadata": {"flow_name": "etl_pipeline"},
            "pattern": {"pattern": "pipeline"},
            "instance": {"instance_id": "inst-pipe"},
        }

    def get_flow(self, flow_id: str, *, verbose: bool = False) -> dict[str, Any]:
        self.calls.append(("get_flow", flow_id, verbose))
        return {
            "name": flow_id,
            "pattern": "pipeline",
            "options": {
                "steps": [
                    {"rule": "trim", "source_key": "raw", "target_key": "clean"},
                    {"rule": "uppercase", "source_key": "clean", "target_key": "out"},
                ]
            },
        }

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        return {"instance_id": instance_id, "root": {"flow": "parent"}}

    def get_health(self) -> dict[str, Any]:
        return {"status": "ok"}

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        return {"jobs": []}


@pytest.fixture
def phase3_server():
    fake = _Phase3FakeClient()
    server = create_mcp_server(
        PalmMcpConfig(base_url="http://127.0.0.1:8080", subject="dev", llms_txt_path=None),
        client=fake,
    )
    return server, fake


@pytest.mark.asyncio
async def test_palm_wizard_collection_action_assistant_format(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_collection_action",
            {"instance_id": "inst-1", "action": "add", "format": "assistant"},
        )
    assert result.data.get("status") == "waiting"
    assert result.data.get("hint") == "Pick a choice or type a value."
    assert "operator_hint" not in result.data


@pytest.mark.asyncio
async def test_palm_wizard_collection_action_add_with_value_one_shot(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_collection_action",
            {"instance_id": "inst-1", "action": "add", "value": "Test Palm"},
        )
    assert ("provide_wizard_input", "inst-1", "Add a new item") in fake.calls
    assert ("provide_wizard_input", "inst-1", "Test Palm") in fake.calls
    assert result.data["collection_action"] == "add"
    assert result.data["collection_phase"] == "menu"


@pytest.mark.asyncio
async def test_palm_wizard_collection_action_tool(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_collection_action",
            {"instance_id": "inst-1", "action": "add"},
        )
    assert ("provide_wizard_input", "inst-1", "Add a new item") in fake.calls
    assert result.data["collection_action"] == "add"
    assert result.data["collection_phase"] == "field"


@pytest.mark.asyncio
async def test_palm_wizard_commit_preview_tool(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_commit_preview",
            {"instance_id": "inst-1"},
        )
    assert ("get_wizard", "inst-1") in fake.calls
    assert result.data["instance_id"] == "inst-1"


@pytest.mark.asyncio
async def test_palm_parallel_branch_status_tool(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_parallel_branch_status",
            {"job_id": "parallel-job"},
        )
    payload = result.data
    assert payload["active_branch"] == "alpha"
    assert len(payload["branches"]) == 2


@pytest.mark.asyncio
async def test_palm_pipeline_step_trace_tool(phase3_server) -> None:
    server, fake = phase3_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_pipeline_step_trace",
            {"job_id": "pipe-job"},
        )
    assert result.data["step_count"] == 2
    assert result.data["steps"][0]["rule"] == "trim"


@pytest.mark.asyncio
async def test_debug_wizard_block_prompt(phase3_server) -> None:
    server, _ = phase3_server
    async with Client(server) as client:
        result = await client.get_prompt("debug-wizard-block", {"instance_id": "inst-1"})
    assert "inst-1" in result.messages[0].content.text
