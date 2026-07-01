"""Tests for GET /v1/jobs/{job_id}/context rich job context endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from palm.common.job_context import build_job_context, derive_next_actions
from palm.common.patterns import PatternBuildContext, build_pattern
from palm.core.orchestration import Job, JobStatus
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance, StateSnapshot
from palm.runtimes.cli.shared.job_inspect import inspect_job_json
from palm.runtimes.server import ServerRuntime

from palm.states import BlackboardState


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
) -> tuple[int, dict[str, Any] | str]:
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
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if "application/json" in exc.headers.get("Content-Type", ""):
            return exc.code, json.loads(raw)
        return exc.code, raw


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="ctx-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Your name?"},
                {"slug": "done", "title": "Done", "prompt": "Done?"},
            ],
        },
    )


def _waiting_wizard_job() -> Job:
    flow = _wizard_flow()
    built = build_pattern(flow, context=PatternBuildContext())
    state = BlackboardState()
    built.tick(state)
    return Job(
        id="job-ctx",
        executable=built,
        state=state,
        status=JobStatus.WAITING_FOR_INPUT,
        metadata={"pattern": "wizard", "instance_id": "inst-ctx"},
    )


def test_build_job_context_includes_pattern_and_actions() -> None:
    job = _waiting_wizard_job()
    instance = ProcessInstance(
        instance_id="inst-ctx",
        job_id="job-ctx",
        status=JobStatus.WAITING_FOR_INPUT.value,
        state_snapshot={},
        flow_definition=_wizard_flow().to_dict(),
        pattern="wizard",
    )
    instance.append_state_snapshot(
        StateSnapshot(
            status="WAITING_FOR_INPUT",
            recorded_at="2026-06-17T12:00:00+00:00",
            state_snapshot={"answers": {}},
            job_id="job-ctx",
            current_step_slug="name",
        )
    )
    instance.append_status(JobStatus.WAITING_FOR_INPUT.value, job_id="job-ctx")

    payload = build_job_context(
        job,
        pattern=inspect_job_json(job),
        instance=instance,
        wizard_progress={
            "current_step": "name",
            "completed_steps": [],
            "updated_at": "2026-06-17T12:00:00+00:00",
            "backtrack_trace": [],
        },
    )

    assert payload["found"] is True
    assert payload["pattern"]["pattern"] == "wizard"
    assert payload["pattern"]["step"] == "name"
    assert payload["instance"]["link"] == "/v1/api/system/instances/inst-ctx"
    assert payload["blackboard_snapshot"]["snapshot_id"] == "0"
    assert any(event["type"] == "instance.status" for event in payload["recent_events"])
    actions = {item["action"] for item in payload["next_actions"]}
    assert "provide_input" in actions
    assert "list_snapshots" in actions


def test_derive_next_actions_for_terminal_job() -> None:
    actions = derive_next_actions(
        "job-1",
        JobStatus.SUCCEEDED,
        "inst-1",
        ProcessInstance(
            instance_id="inst-1",
            job_id="job-1",
            status="SUCCEEDED",
            state_snapshot={},
            flow_definition={},
            pattern="wizard",
        ),
    )
    names = {item["action"] for item in actions}
    assert "resume_instance" in names
    assert "provide_input" not in names


def test_get_job_context_after_submit(server: ServerRuntime) -> None:
    status, payload = _request(
        server.base_url,
        "POST",
        "/v1/api/flows/onboard/create",
        body={"wizard": {"name": "onboard", "steps": 2}},
    )
    assert status in {200, 202}
    assert isinstance(payload, dict)
    job_id = payload["job_id"]

    status, slim = _request(server.base_url, "GET", f"/v1/api/system/jobs/{job_id}")
    assert status == 200
    assert isinstance(slim, dict)
    assert "pattern" not in slim
    assert "next_actions" not in slim

    status, context = _request(server.base_url, "GET", f"/v1/api/system/jobs/{job_id}/context")
    assert status == 200
    assert isinstance(context, dict)
    assert context["found"] is True
    assert context["job_id"] == job_id
    assert context["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert "pattern" in context
    assert "instance" in context
    assert context["instance"]["link"].startswith("/v1/api/system/instances/")
    assert "next_actions" in context
    assert any(item["action"] == "provide_input" for item in context["next_actions"])


def test_get_job_context_not_found(server: ServerRuntime) -> None:
    status, payload = _request(server.base_url, "GET", "/v1/api/system/jobs/missing-job/context")
    assert status == 404
    assert isinstance(payload, dict)
    assert payload["error"] == "job_not_found"


def test_docs_include_job_context_route() -> None:
    from palm.runtimes.server.surfaces.rest.system.routes import ROUTES

    routes = {entry.route_id: entry for entry in ROUTES}
    route = routes["inspect_job"]
    assert route.path == "/v1/api/system/jobs/{job_id}/context"
    from palm.runtimes.server.surfaces.rest.doc_examples import RESPONSE_EXAMPLES

    assert "get_job_context" in RESPONSE_EXAMPLES
