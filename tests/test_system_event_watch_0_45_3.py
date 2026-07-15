"""0.45.3 — system event watchdog definitions + loop guards."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from examples.definitions.coconut.profile_pipeline import COCONUT_PROFILE_PIPELINE
from examples.definitions.system.event_watch import (
    _WATCH_FLOW,
    PALM_SYSTEM_EVENTS_WATCH,
)
from examples.definitions.system.event_watch import (
    register_definitions as register_event_watch,
)
from palm.app import ApplicationHost, PalmSettings
from palm.common.patterns import build_pattern
from palm.common.transforms import autoload
from palm.core import PatternStatus
from palm.core.transform.engine import TransformEngine
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState
from tests.helpers.event_plane import emit_orchestration_event


@pytest.fixture
def transform_engine() -> Iterator[TransformEngine]:
    transform_registry.clear()
    autoload()
    engine = TransformEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


def _register_watch(host: ApplicationHost) -> None:
    register_event_watch(host.app.repository())
    host.reload_inbound_bindings()


def _log_events(host: ApplicationHost) -> list:
    result = host.invoke_resource("palm-system-event-log", action="get")
    if not result.success:
        return []
    data = result.data
    if isinstance(data, dict):
        value = data.get("value")
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
    return data if isinstance(data, list) else []


def _drain_all(host: ApplicationHost) -> None:
    while host.work_drain.store.pending_count():
        host.work_drain.tick(limit=20)
    host._execution.flows.wait_until_idle(timeout=10.0)


def _emit_job_completed(host: ApplicationHost, **payload: object) -> None:
    """Emit on the runtime orchestration bus (where real jobs publish)."""
    emit_orchestration_event(host, "job.completed", **payload)


def test_event_watch_definitions_parse() -> None:
    inbound = (PALM_SYSTEM_EVENTS_WATCH.metadata or {}).get("inbound") or {}
    assert inbound.get("mode") == "internal"
    assert "resource.changed" not in (inbound.get("event_types") or [])
    assert inbound.get("work", {}).get("flow_id") == _WATCH_FLOW


def test_conditional_passthrough_keeps_row(transform_engine) -> None:
    state = TestState()
    state.set("row", {"resource_ref": "palm-todos", "flow": "quick"})
    transform_engine.apply_to_state(
        "conditional",
        state,
        "row",
        target_key="row",
        field="resource_ref",
        not_equals="palm-system-event-log",
        passthrough=True,
        **{"else": None},
    )
    assert state.get("row", {}).get("resource_ref") == "palm-todos"


def test_watch_records_external_job_completed() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        _emit_job_completed(
            host,
            job_id="job-ext-1",
            flow="quick",
            status="SUCCEEDED",
        )
        _drain_all(host)
        events = _log_events(host)
        assert len(events) >= 1
        assert events[0].get("type") == "job.completed"
    finally:
        host.shutdown()


def test_watch_appends_multiple_events_as_list() -> None:
    """put_resource (BATCH mode) must persist the full list tail, not per-item puts."""
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        host.invoke_resource(
            "palm-system-event-log",
            action="put",
            params={"value": []},
        )
        for job_id, flow in (("job-a", "quick"), ("job-b", "onboard")):
            _emit_job_completed(
                host,
                job_id=job_id,
                flow=flow,
                status="SUCCEEDED",
            )
            _drain_all(host)
            # isolate kv tail from other tests (memory backend is process-global)
            if job_id == "job-a":
                raw = host.invoke_resource("palm-system-event-log", action="get")
                value = (raw.data or {}).get("value")
                assert isinstance(value, list)
                assert len(value) == 1

        raw = host.invoke_resource("palm-system-event-log", action="get")
        assert raw.success
        value = (raw.data or {}).get("value")
        assert isinstance(value, list), f"expected list tail in kv, got {type(value).__name__}"
        assert len(value) >= 2
        job_ids = {row.get("job_id") for row in value if isinstance(row, dict)}
        assert {"job-a", "job-b"} <= job_ids
    finally:
        host.shutdown()


def test_watch_ignores_self_flow_completion() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        _emit_job_completed(host, job_id="job-a", flow="quick", status="SUCCEEDED")
        _drain_all(host)
        count_after_external = len(_log_events(host))

        _emit_job_completed(
            host,
            job_id="job-self",
            flow=_WATCH_FLOW,
            status="SUCCEEDED",
        )
        _drain_all(host)
        assert len(_log_events(host)) == count_after_external
    finally:
        host.shutdown()


def test_watch_ingress_skips_self_job_completed() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        host.invoke_resource(
            "palm-system-event-log",
            action="put",
            params={"value": []},
        )
        _emit_job_completed(
            host,
            job_id="job-self-ingress",
            flow=_WATCH_FLOW,
            status="SUCCEEDED",
        )
        _drain_all(host)
        pending = [
            intent
            for intent in host.work_drain.store.list_pending(limit=20)
            if intent.target == _WATCH_FLOW
        ]
        assert pending == []
        assert host.invoke_resource("palm-system-event-log", action="get").data.get(
            "value"
        ) in ([], None)
    finally:
        host.shutdown()


def test_resource_changed_does_not_enqueue_watch() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        _register_watch(host)
        emit_orchestration_event(
            host,
            "resource.changed",
            resource_ref="palm-system-event-log",
            action="put",
            provider="kv",
        )
        pending = host.work_drain.store.list_pending(limit=20)
        assert not any(intent.target == _WATCH_FLOW for intent in pending)
    finally:
        host.shutdown()


def test_coconut_profile_pipeline_slice() -> None:
    transform_registry.clear()
    autoload()
    pattern = build_pattern(COCONUT_PROFILE_PIPELINE)
    state = TestState()
    state.set("player_profile", {"visit_count": 2, "player_name": "Ada"})
    state.set("player_name", "Ada")
    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert state.get("is_returning") is True
    assert "remember" in str(state.get("player_profile", {}).get("returning_note", ""))