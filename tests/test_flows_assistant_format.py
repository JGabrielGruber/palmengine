"""Flows opt-in assistant view format — REST and MCP (0.21.5)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

fastmcp = pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from palm.common.operator.flow_session_view import shape_flow_session_view  # noqa: E402
from palm.common.operator.view_registry import clear_operator_view_builders  # noqa: E402
from palm.runtimes.mcp.assist.dispatch import shape_dispatch_result  # noqa: E402
from palm.runtimes.mcp.config import PalmMcpConfig  # noqa: E402
from palm.runtimes.mcp.in_process import (  # noqa: E402
    PalmInProcessBackend,
    shutdown_in_process_runtime,
)
from palm.runtimes.mcp.server import create_mcp_server  # noqa: E402
from palm.runtimes.server import ServerRuntime  # noqa: E402
from palm.runtimes.server.factory import build_server_context  # noqa: E402
from palm.services.assist.views import ensure_assist_view_registration  # noqa: E402
from palm.services.execution.flows.schemas import SessionContext  # noqa: E402


def _onboard_flat() -> dict[str, Any]:
    return {
        "session_id": "inst-1",
        "instance_id": "inst-1",
        "job_id": "job-1",
        "flow_name": "onboard",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "intro",
        "prompt": {
            "step": "intro",
            "text": "What is your name?",
            "field_type": "text",
            "step_kind": "input",
        },
        "answers": {},
    }


def _setup_assistant_registry() -> None:
    clear_operator_view_builders()
    ensure_assist_view_registration()


def test_shape_flow_session_view_powertool_default() -> None:
    _setup_assistant_registry()
    payload = shape_flow_session_view(_onboard_flat())
    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "intro"
    assert "operator_hint" in payload
    assert "question" not in payload


def test_shape_flow_session_view_assistant_opt_in() -> None:
    _setup_assistant_registry()
    payload = shape_flow_session_view(
        _onboard_flat(),
        format="assistant",
        session_id="inst-1",
        flow_id="onboard",
    )
    assert payload["question"] == "What is your name?"
    assert payload["status"] == "waiting"
    assert "operator_hint" not in payload
    assert payload.get("scenario_id") is None


def test_shape_dispatch_result_flows_input_assistant_from_params() -> None:
    _setup_assistant_registry()
    ctx = SessionContext(
        session_id="inst-1",
        flow_id="onboard",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        pattern="wizard",
        waiting_for_input=True,
        detail=_onboard_flat(),
    )
    payload = shape_dispatch_result(
        ["flows", "onboard", "session", "inst-1", "input"],
        ctx,
        params={"format": "assistant"},
    )
    assert payload["question"] == "What is your name?"
    assert "operator_hint" not in payload


def test_shape_dispatch_result_flows_assistant_from_params() -> None:
    _setup_assistant_registry()
    ctx = SessionContext(
        session_id="inst-1",
        flow_id="onboard",
        job_id="job-1",
        status="WAITING_FOR_INPUT",
        pattern="wizard",
        waiting_for_input=True,
        detail=_onboard_flat(),
    )
    payload = shape_dispatch_result(
        ["flows", "onboard", "session", "inst-1"],
        ctx,
        params={"format": "assistant"},
    )
    assert payload["question"] == "What is your name?"
    assert "operator_hint" not in payload


@pytest.fixture
def flows_server_ctx():
    from palm.app.bootstrap import load_definitions_for_repository

    shutdown_in_process_runtime()
    from palm.app.settings import PalmSettings

    settings = PalmSettings.for_tests(load_examples=True)
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(http=False)
    load_definitions_for_repository(rt.repository, settings)
    ctx = build_server_context(rt)
    yield ctx
    rt.stop()
    shutdown_in_process_runtime()


@pytest.mark.asyncio
async def test_palm_flows_session_assistant_in_process(flows_server_ctx) -> None:
    backend = PalmInProcessBackend(flows_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        started = await client.call_tool(
            "palm_flows_create_session",
            {"flow_id": "onboard"},
        )
        session_id = started.data["session_id"]
        result = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "flow_id": "onboard", "format": "assistant"},
        )

    payload = result.data
    assert payload.get("question")
    assert payload.get("status") == "waiting"
    assert "operator_hint" not in payload


@pytest.mark.asyncio
async def test_palm_flows_session_powertool_default_in_process(flows_server_ctx) -> None:
    backend = PalmInProcessBackend(flows_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        started = await client.call_tool(
            "palm_flows_create_session",
            {"flow_id": "onboard"},
        )
        session_id = started.data["session_id"]
        result = await client.call_tool(
            "palm_flows_session",
            {"session_id": session_id, "flow_id": "onboard"},
        )

    payload = result.data
    assert payload.get("step")
    assert "operator_hint" in payload
    assert "question" not in payload


@pytest.fixture
def server() -> ServerRuntime:
    rt = ServerRuntime(host="127.0.0.1", port=0)
    rt.start(port=0)
    yield rt
    rt.stop()


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload


def test_flows_rest_session_assistant_opt_in(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    session_id = created["session_id"]

    status, payload = _request(
        server.base_url,
        "GET",
        f"/v1/api/flows/onboard/session/{session_id}?format=assistant",
    )
    assert status == 200
    assert payload.get("question")
    assert payload.get("status") == "waiting"
    assert "operator_hint" not in payload


@pytest.mark.asyncio
async def test_palm_flows_session_input_assistant_format(flows_server_ctx) -> None:
    backend = PalmInProcessBackend(flows_server_ctx)
    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
    )
    server = create_mcp_server(config, client=backend)

    async with Client(server) as client:
        started = await client.call_tool(
            "palm_flows_create_session",
            {"flow_id": "onboard"},
        )
        session_id = started.data["session_id"]
        result = await client.call_tool(
            "palm_flows_session_input",
            {
                "session_id": session_id,
                "flow_id": "onboard",
                "input": "Ada",
                "format": "assistant",
            },
        )

    payload = result.data
    assert payload.get("question")
    assert payload.get("status") == "waiting"
    assert "operator_hint" not in payload


def test_flows_rest_session_input_assistant_opt_in(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    session_id = created["session_id"]

    status, payload = _request(
        server.base_url,
        "POST",
        f"/v1/api/flows/onboard/session/{session_id}/input?format=assistant",
        body={"value": "Ada"},
    )
    assert status == 200
    assert payload.get("question")
    assert payload.get("status") == "waiting"
    assert "operator_hint" not in payload


def test_flows_rest_session_powertool_default(server: ServerRuntime) -> None:
    status, created = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    session_id = created["session_id"]

    status, payload = _request(
        server.base_url,
        "GET",
        f"/v1/api/flows/onboard/session/{session_id}",
    )
    assert status == 200
    assert payload.get("step")
    assert "operator_hint" in payload
    assert "question" not in payload