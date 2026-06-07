"""Tests for AuthMiddleware and drive authorization."""

from __future__ import annotations

import pytest

from palm.core.auth import AuthEngine, Principal
from palm.core.orchestration import JobStatus, OrchestrationEngine
from palm.core.orchestration.exceptions import JobAuthorizationError
from palm.definitions.flow import FlowDefinition
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.hooks import AuthMiddleware
from tests.core.fakes.mode import TestMode
from tests.core.fakes.runner import TestRunner


def test_auth_middleware_stamps_principal_on_submit() -> None:
    rt = EmbeddedRuntime()
    rt.start(
        runner=TestRunner(),
        credentials={"subject": "ada"},
        auth_enforce=True,
    )
    try:
        job = rt.orchestration.submit({"steps": 1, "final_status": "SUCCEEDED"})
        assert job.metadata["principal_id"] == "ada"
        assert job.status == JobStatus.SUCCEEDED
    finally:
        rt.stop()


def test_auth_middleware_rejects_unauthenticated_drive() -> None:
    auth = AuthEngine()
    auth.initialize()
    hook = AuthMiddleware(auth, enforce_drive=True)
    engine = OrchestrationEngine()
    engine.initialize(scheduler=TestMode(runner=TestRunner()), hooks=[hook])
    engine.start()

    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED"})
    assert job.status == JobStatus.FAILED
    assert isinstance(job.error, JobAuthorizationError)

    engine.stop()
    engine.shutdown()
    auth.shutdown()


def test_auth_middleware_allows_bound_principal() -> None:
    auth = AuthEngine()
    auth.initialize()
    auth.bind_principal(Principal(id="ops", roles=("user", "admin")))
    hook = AuthMiddleware(auth, required_roles=("admin",))
    engine = OrchestrationEngine()
    engine.initialize(scheduler=TestMode(runner=TestRunner()), hooks=[hook])
    engine.start()

    job = engine.submit({"steps": 1, "final_status": "SUCCEEDED", "result": "ok"})
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == "ok"

    engine.stop()
    engine.shutdown()
    auth.shutdown()


def test_embedded_auth_enforce_requires_credentials() -> None:
    rt = EmbeddedRuntime()
    rt.start(runner=TestRunner(), auth_enforce=True)
    try:
        job = rt.orchestration.submit({"steps": 1, "final_status": "SUCCEEDED"})
        assert job.status == JobStatus.FAILED
    finally:
        rt.stop()


def test_prepare_flow_plan_requires_started() -> None:
    rt = EmbeddedRuntime()
    with pytest.raises(RuntimeError, match="Runtime host is not started"):
        rt.executor.prepare_flow_plan(
            FlowDefinition(name="x", pattern="wizard", options={"steps": 1}),
        )