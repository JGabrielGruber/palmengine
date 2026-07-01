"""Tests for Palm provider refactoring — typed params, coordinator, remote errors."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from palm.providers.palm.bindings.orchestration.local import LocalPalmInvoker
from palm.providers.palm.bindings.orchestration.payload import remote_job_payload
from palm.providers.palm.exceptions import PalmRemoteError, PalmTimeoutError
from palm.providers.palm.flow.coordinator import PalmInvokeCoordinator
from palm.providers.palm.flow.params import PalmInvokeParams
from palm.providers.palm.flow.remote import client as remote_module
from palm.providers.palm.flow.remote.invoker import RemotePalmInvoker


def test_palm_invoke_params_wait_mode_until_input() -> None:
    params = PalmInvokeParams.from_mapping(
        {"flow_name": "child-wizard", "wait_mode": "until_input", "timeout_seconds": 42},
    )
    assert params.wait is True
    assert params.wait_mode == "until_input"
    assert params.wait_timeout == 42.0
    assert params.resolved_wait_mode.value == "until_input"


def test_palm_invoke_params_fire_and_forget_by_default() -> None:
    params = PalmInvokeParams.from_mapping({"flow_name": "child-wizard"})
    assert params.wait is False
    assert params.resolved_wait_mode.value == "fire_and_forget"


def test_palm_invoke_params_from_mapping_typed_fields() -> None:
    params = PalmInvokeParams.from_mapping(
        {
            "flow_name": "ingest-etl",
            "wait": "true",
            "wait_timeout": "12.5",
            "max_depth": "4",
            "remote_retries": "1",
            "__palm:parent_job_id": "parent-1",
            "custom_child_key": "value",
        },
        resource_id="flow:ingest-etl",
    )
    assert params.flow_name == "ingest-etl"
    assert params.resource_id == "flow:ingest-etl"
    assert params.wait is True
    assert params.wait_timeout == 12.5
    assert params.max_depth == 4
    assert params.remote_retries == 1
    assert params.parent_job_id == "parent-1"
    assert params.extras == {"custom_child_key": "value"}


def test_palm_invoke_params_target_dict() -> None:
    params = PalmInvokeParams(
        flow_name="ingest-etl", by_id=True, target_kind="flow", target="ingest-etl"
    )
    assert params.as_target_dict() == {
        "by_id": True,
        "target_kind": "flow",
        "kind": None,
        "target": "ingest-etl",
        "flow_name": "ingest-etl",
        "process_name": None,
        "resource_ref": None,
        "name": None,
    }


def test_palm_invoke_params_correlation_metadata() -> None:
    params = PalmInvokeParams(metadata={"trace": "abc"}, parent_job_id="parent-9")
    meta = params.correlation_metadata(depth=2, chain=("flow:a", "flow:b"))
    assert meta["trace"] == "abc"
    assert meta["__palm:invoke_depth"] == 2
    assert meta["__palm:invoke_chain"] == ["flow:a", "flow:b"]
    assert meta["__palm:parent_job_id"] == "parent-9"


def test_remote_request_retries_transient_status() -> None:
    responses = [(503, {"error": "unavailable"}), (202, {"job_id": "job-1", "status": "SUCCEEDED"})]

    def fake_request(*_args: object, **_kwargs: object) -> tuple[int, dict[str, object]]:
        return responses.pop(0)

    with patch.object(remote_module, "_request", side_effect=fake_request):
        status, payload = remote_module._request_with_retry(
            "http://localhost:8080",
            "POST",
            "/v1/api/flows/onboard/create",
            retries=2,
        )
    assert status == 202
    assert payload["job_id"] == "job-1"


def test_remote_request_raises_palm_remote_error() -> None:
    with patch.object(remote_module, "_request", return_value=(404, {"error": "missing"})):
        with pytest.raises(PalmRemoteError) as exc_info:
            remote_module.submit_flow_remote("http://localhost:8080", "missing-flow", retries=0)
    assert exc_info.value.status_code == 404
    assert exc_info.value.transient is False


def test_wait_for_job_remote_raises_palm_timeout() -> None:
    with patch.object(
        remote_module,
        "get_job_remote",
        return_value={"job_id": "job-1", "status": "RUNNING"},
    ):
        with pytest.raises(PalmTimeoutError):
            remote_module.wait_for_job_remote(
                "http://localhost:8080",
                "job-1",
                timeout=0.01,
                poll_interval=0.0,
                retries=0,
            )


@patch.object(remote_module, "_request_with_retry")
def test_submit_flow_remote_uses_api_create(mock_request) -> None:
    mock_request.return_value = (
        202,
        {"session_id": "inst-1", "job_id": "job-1", "status": "RUNNING"},
    )
    remote_module.submit_flow_remote("http://localhost:8080", "onboard", retries=0)
    args = mock_request.call_args[0]
    assert args[2] == "/v1/api/flows/onboard/create"


@patch.object(remote_module, "_request_with_retry")
def test_get_job_remote_uses_system_path(mock_request) -> None:
    mock_request.return_value = (200, {"job_id": "job-1", "status": "SUCCEEDED"})
    remote_module.get_job_remote("http://localhost:8080", "job-1", retries=0)
    args = mock_request.call_args[0]
    assert args[2] == "/v1/api/system/jobs/job-1"


@patch.object(remote_module, "_request_with_retry")
def test_submit_process_remote_uses_process_api(mock_request) -> None:
    mock_request.side_effect = [
        (200, {"plans": [{"plan_id": "plan-1"}]}),
        (202, {"jobs": [{"job_id": "job-1", "status": "RUNNING"}]}),
    ]
    remote_module.submit_process_remote(
        "http://localhost:8080",
        "onboarding",
        retries=0,
    )
    prepare_args = mock_request.call_args_list[0][0]
    submit_args = mock_request.call_args_list[1][0]
    assert prepare_args[2] == "/v1/api/processes/onboarding/prepare"
    assert submit_args[2] == "/v1/api/processes/submit"


def test_remote_job_payload_maps_session_id_to_instance_id() -> None:
    payload = remote_job_payload(
        {"job_id": "job-1", "session_id": "inst-1", "status": "RUNNING"},
    )
    assert payload["instance_id"] == "inst-1"


def test_coordinator_exposes_invoker_strategies() -> None:
    local = LocalPalmInvoker()
    remote = RemotePalmInvoker()
    coordinator = PalmInvokeCoordinator(local=local, remote=remote)
    assert coordinator._local is local
    assert coordinator._remote is remote
