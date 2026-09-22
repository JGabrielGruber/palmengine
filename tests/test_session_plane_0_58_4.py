"""0.58.4 — Job path link: instance session owner + event attribution + plane attach."""

from __future__ import annotations

from palm.common.events.reliable import event_context_from_job
from palm.common.patterns import PatternBuildContext
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.persistence.instance_sync import (
    build_instance_from_job,
    session_id_from_job_metadata,
)
from palm.core.event import EventContext
from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.engine import OrchestrationEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState
from palm.system.executions.flow_submission import prepare_flow_submission


def test_session_id_from_job_metadata() -> None:
    assert session_id_from_job_metadata({"session_id": "sess-a"}) == "sess-a"
    # 0.58.9 — no palm_session_id dual; ignored if present
    assert session_id_from_job_metadata({"palm_session_id": "sess-b"}) is None
    assert session_id_from_job_metadata({}) is None
    assert session_id_from_job_metadata({"session_id": "  "}) is None


def test_process_instance_session_id_roundtrip() -> None:
    inst = ProcessInstance(
        instance_id="inst-1",
        job_id="job-1",
        status="RUNNING",
        state_snapshot={},
        flow_definition={"name": "x", "pattern": "wizard", "options": {}},
        pattern="wizard",
        session_id="sess-owner",
    )
    data = inst.to_dict()
    assert data["session_id"] == "sess-owner"
    back = ProcessInstance.from_dict(data)
    assert back.session_id == "sess-owner"
    assert back.resolved_session_id() == "sess-owner"
    assert back.session_id != back.instance_id


def test_process_instance_session_id_from_legacy_metadata() -> None:
    data = {
        "instance_id": "inst-legacy",
        "job_id": "job-1",
        "status": "RUNNING",
        "state_snapshot": {},
        "flow_definition": {"name": "x", "pattern": "wizard", "options": {}},
        "pattern": "wizard",
        "metadata": {"session_id": "sess-from-meta"},
    }
    back = ProcessInstance.from_dict(data)
    assert back.session_id == "sess-from-meta"
    assert back.resolved_session_id() == "sess-from-meta"


def test_build_instance_from_job_sets_session_id() -> None:
    flow = FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1})
    job = Job(
        id="job-1",
        executable=object(),
        state=BlackboardState(),
        metadata={
            "pattern": "wizard",
            "instance_id": "inst-1",
            "session_id": "sess-build",
        },
        status=JobStatus.WAITING_FOR_INPUT,
    )
    instance = build_instance_from_job(job, flow=flow, instance_id="inst-1")
    assert instance.session_id == "sess-build"
    assert instance.metadata["session_id"] == "sess-build"
    assert instance.session_id != instance.instance_id


def test_prepare_flow_submission_normalizes_session_id() -> None:
    repo = DefinitionRepository()
    flow = repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1}),
    )
    submission = prepare_flow_submission(
        flow,
        state=None,
        metadata={"session_id": "sess-prep"},
        instances=None,
        build_ctx=PatternBuildContext(definition_repository=repo),
        instance_id="inst-prep",
    )
    assert submission.metadata["session_id"] == "sess-prep"
    assert submission.metadata["instance_id"] == "inst-prep"
    # 0.58.9 — palm_session_id is not normalized into session_id
    bare = prepare_flow_submission(
        flow,
        state=None,
        metadata={"palm_session_id": "sess-ignored"},
        instances=None,
        build_ctx=PatternBuildContext(definition_repository=repo),
        instance_id="inst-prep-2",
    )
    assert "session_id" not in bare.metadata or bare.metadata.get("session_id") != "sess-ignored"


def test_event_context_carries_session_id() -> None:
    ctx = EventContext(job_id="j1", instance_id="i1", session_id="s1")
    data = ctx.to_dict()
    assert data["session_id"] == "s1"
    back = EventContext.from_dict(data)
    assert back is not None
    assert back.session_id == "s1"
    merged = EventContext(job_id="j1").merged(EventContext(session_id="s2"))
    assert merged.session_id == "s2"

    job = Job(
        id="j1",
        executable=object(),
        state=BlackboardState(),
        metadata={"instance_id": "i1", "session_id": "sess-ctx"},
    )
    from_job = event_context_from_job(job)
    assert from_job.session_id == "sess-ctx"
    assert from_job.instance_id == "i1"
    eng_ctx = OrchestrationEngine._event_context_from_job(job)
    assert eng_ctx.session_id == "sess-ctx"


def test_flow_session_terminal_payload_includes_session_and_instance() -> None:
    from palm.core.event import EventEngine

    bus = EventEngine()
    bus.initialize()
    captured: list[dict] = []
    bus.subscribe("*", lambda e: captured.append(e.enriched_payload()))

    orch = OrchestrationEngine()
    orch.initialize(event_engine=bus, hooks=[])
    job = Job(
        id="job-term",
        executable=object(),
        state=BlackboardState(),
        metadata={
            "flow": "demo",
            "instance_id": "inst-term",
            "session_id": "sess-term",
        },
        status=JobStatus.SUCCEEDED,
    )
    orch._emit_flow_session_terminal(job)
    types = [c.get("type") or "" for c in captured]
    # enriched may use event type separately — check payload fields
    assert any(
        c.get("session_id") == "sess-term" and c.get("instance_id") == "inst-term"
        for c in captured
    )
    assert any(
        OrchestrationEventType.FLOW_SESSION_SUCCEEDED in str(c)
        or c.get("status") == "SUCCEEDED"
        for c in captured
    )
    bus.shutdown()
    orch.shutdown()


def test_embedded_submit_attaches_instance_under_session() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plane = rt.session_plane
        assert plane is not None
        bind = plane.bind(surface="test")
        sess = bind.session_id

        flow = FlowDefinition(
            name="sess_link_demo",
            pattern="wizard",
            options={
                "steps": [
                    {"slug": "only", "title": "Only", "prompt": "ok?"},
                ]
            },
        )
        job = rt.submit_flow(
            flow,
            metadata={"session_id": sess},
        )
        iid = str(job.metadata.get("instance_id") or "")
        assert iid
        assert job.metadata.get("session_id") == sess
        assert sess != iid

        # Plane multi-attach
        owner = plane.session_for_instance(iid)
        assert owner is not None
        assert owner.session_id == sess
        assert iid in plane.list_instances(sess)

        # Durable instance record
        inst = rt.instance_manager.get(iid)
        assert inst.session_id == sess or inst.resolved_session_id() == sess
        assert inst.session_id != inst.instance_id
    finally:
        rt.stop()
        clear_palm_runtime()


def test_multi_instance_under_one_session() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    try:
        plane = rt.session_plane
        assert plane is not None
        sess = plane.bind(surface="test").session_id
        flow = FlowDefinition(
            name="multi_sess",
            pattern="wizard",
            options={"steps": [{"slug": "a", "title": "A", "prompt": "?"}]},
        )
        j1 = rt.submit_flow(flow, metadata={"session_id": sess})
        j2 = rt.submit_flow(flow, metadata={"session_id": sess})
        i1 = str(j1.metadata["instance_id"])
        i2 = str(j2.metadata["instance_id"])
        assert i1 != i2
        assert set(plane.list_instances(sess)) >= {i1, i2}
    finally:
        rt.stop()
        clear_palm_runtime()
