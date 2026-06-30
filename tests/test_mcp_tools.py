"""Tests for the Palm FastMCP stdio adapter (REST proxy / ``PalmRestClient`` path).

Uses ``_FakeRestClient`` — the HTTP round-trip mode when ``PALM_MCP_IN_PROCESS=0``.
In-process service calls are covered in ``tests/test_mcp_in_process.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.rest_client import PalmRestError  # noqa: E402
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402


class _FakeRestClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        self.calls.append(("list_waiting_jobs", limit))
        return {
            "jobs": [
                {
                    "job_id": "job-1",
                    "status": "WAITING_FOR_INPUT",
                    "metadata": {
                        "instance_id": "inst-1",
                        "pattern": "wizard",
                        "flow_name": "onboard",
                    },
                }
            ]
        }

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        self.calls.append(("get_wizard", instance_id))
        return {
            "instance_id": instance_id,
            "job_id": "job-1",
            "flow_name": "onboard",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "step_1",
            "prompt": {"step": "step_1", "text": "Name?", "field_type": "text"},
            "answers": {},
            "next_actions": [],
        }

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        self.calls.append(("provide_wizard_input", instance_id, value))
        view = self.get_wizard(instance_id)
        view["answers"] = {"step_1": value}
        return view

    def resume_child_wait(self, instance_id: str) -> dict[str, Any]:
        self.calls.append(("resume_child_wait", instance_id))
        return self.get_wizard(instance_id)

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        self.calls.append(("get_instance_tree", instance_id))
        return {"instance_id": instance_id, "root": {"flow": "onboard"}}

    def get_health(self) -> dict[str, Any]:
        return {"status": "ok"}


@pytest.fixture
def mcp_server():
    fake = _FakeRestClient()
    server = create_mcp_server(
        PalmMcpConfig(base_url="http://127.0.0.1:8080", subject="dev", llms_txt_path=None),
        client=fake,
    )
    return server, fake


@pytest.mark.asyncio
async def test_palm_list_waiting_tool(mcp_server) -> None:
    server, fake = mcp_server
    async with Client(server) as client:
        result = await client.call_tool("palm_list_waiting", {"flow": "onboard"})
    assert fake.calls[0][0] == "list_waiting_jobs"
    payload = result.data
    assert payload["count"] == 1
    assert payload["jobs"][0]["instance_id"] == "inst-1"


@pytest.mark.asyncio
async def test_palm_list_waiting_omits_instance_id_when_unknown(mcp_server) -> None:
    server, fake = mcp_server

    def list_without_instance(*, limit: int = 50) -> dict[str, Any]:
        return {
            "jobs": [
                {
                    "job_id": "job-7bd386ce7f3c",
                    "status": "WAITING_FOR_INPUT",
                    "metadata": {},
                }
            ]
        }

    fake.list_waiting_jobs = list_without_instance  # type: ignore[method-assign]

    async with Client(server) as client:
        result = await client.call_tool("palm_list_waiting", {})
    job = result.data["jobs"][0]
    assert job["job_id"] == "job-7bd386ce7f3c"
    assert "instance_id" not in job


@pytest.mark.asyncio
async def test_palm_inspect_instance_tool(mcp_server) -> None:
    server, fake = mcp_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_inspect_instance",
            {"instance_id": "inst-1", "format": "compact"},
        )
    assert fake.calls[-1] == ("get_wizard", "inst-1")
    payload = result.data
    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "step_1"


@pytest.mark.asyncio
async def test_palm_wizard_input_tool(mcp_server) -> None:
    server, fake = mcp_server
    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_input",
            {"instance_id": "inst-1", "input": "Ada"},
        )
    assert ("provide_wizard_input", "inst-1", "Ada") in fake.calls
    payload = result.data
    assert payload["answers_preview"]["step_1"] == "Ada"


@pytest.mark.asyncio
async def test_palm_wizard_input_coerces_confirm(mcp_server) -> None:
    server, fake = mcp_server

    def get_wizard(instance_id: str) -> dict[str, Any]:
        return {
            "instance_id": instance_id,
            "flow_name": "onboard",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "confirm",
            "prompt": {"step": "confirm", "field_type": "confirm"},
            "answers": {},
            "next_actions": [],
        }

    fake.get_wizard = get_wizard  # type: ignore[method-assign]

    async with Client(server) as client:
        await client.call_tool(
            "palm_wizard_input",
            {"instance_id": "inst-1", "input": "yes"},
        )
    assert ("provide_wizard_input", "inst-1", True) in fake.calls


@pytest.mark.asyncio
async def test_palm_wizard_drive_tool(mcp_server) -> None:
    server, fake = mcp_server
    state = {"done": False}

    def get_wizard(instance_id: str) -> dict[str, Any]:
        status = "SUCCESS" if state["done"] else "WAITING_FOR_INPUT"
        return {
            "instance_id": instance_id,
            "flow_name": "onboard",
            "status": status,
            "current_step_slug": "step_1",
            "prompt": {"step": "step_1", "field_type": "text"},
            "answers": {"step_1": "Ada"} if state["done"] else {},
            "next_actions": [],
        }

    def provide_wizard_input(instance_id: str, value: Any) -> dict[str, Any]:
        fake.calls.append(("provide_wizard_input", instance_id, value))
        state["done"] = True
        return get_wizard(instance_id)

    fake.get_wizard = get_wizard  # type: ignore[method-assign]
    fake.provide_wizard_input = provide_wizard_input  # type: ignore[method-assign]

    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_drive",
            {"instance_id": "inst-1", "inputs": ["Ada"]},
        )
    payload = result.data
    assert payload["stopped_reason"] == "terminal"
    assert payload["steps_applied"] == 1


@pytest.mark.asyncio
async def test_palm_wizard_drive_accepts_payload_without_inputs(mcp_server) -> None:
    server, fake = mcp_server
    state = {"done": False}

    def get_wizard(instance_id: str) -> dict[str, Any]:
        status = "SUCCESS" if state["done"] else "WAITING_FOR_INPUT"
        return {
            "instance_id": instance_id,
            "flow_name": "batch",
            "status": status,
            "current_step_slug": "batch_payload",
            "prompt": {"step": "batch_payload", "field_type": "text"},
            "answers": {} if not state["done"] else {"batch_payload": {"main": {}}},
            "next_actions": [],
        }

    def provide_wizard_input(instance_id: str, value: Any) -> dict[str, Any]:
        fake.calls.append(("provide_wizard_input", instance_id, value))
        state["done"] = True
        return get_wizard(instance_id)

    fake.get_wizard = get_wizard  # type: ignore[method-assign]
    fake.provide_wizard_input = provide_wizard_input  # type: ignore[method-assign]

    async with Client(server) as client:
        result = await client.call_tool(
            "palm_wizard_drive",
            {
                "instance_id": "inst-1",
                "payload": {"main": {"title": "MCP Servers for LLMs"}},
            },
        )

    assert result.data["stopped_reason"] == "terminal"
    assert fake.calls == [
        ("provide_wizard_input", "inst-1", {"main": {"title": "MCP Servers for LLMs"}}),
    ]


@pytest.mark.asyncio
async def test_palm_wizard_drive_requires_inputs_or_payload(mcp_server) -> None:
    server, _ = mcp_server
    async with Client(server) as client:
        with pytest.raises(Exception, match="inputs or payload"):
            await client.call_tool("palm_wizard_drive", {"instance_id": "inst-1"})


@pytest.mark.asyncio
async def test_palm_resume_child_wait_skips_when_not_waiting(mcp_server) -> None:
    server, fake = mcp_server

    def resume_child_wait(instance_id: str) -> dict[str, Any]:
        raise PalmRestError(400, "Instance 'inst-1' is not waiting for a nested child")

    fake.resume_child_wait = resume_child_wait  # type: ignore[method-assign]

    async with Client(server) as client:
        result = await client.call_tool("palm_resume_child_wait", {"instance_id": "inst-1"})
    payload = result.data
    assert payload["resume_child_wait"] == "skipped_not_waiting"
    assert payload["instance_id"] == "inst-1"


@pytest.mark.asyncio
async def test_instance_tree_resource(mcp_server) -> None:
    server, fake = mcp_server
    async with Client(server) as client:
        result = await client.read_resource("palm://instances/inst-1/tree")
    assert ("get_instance_tree", "inst-1") in fake.calls
    assert "onboard" in result[0].text
