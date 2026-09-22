"""0.58.8 — Session watches / fan-in + continue resolve from attach list."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.event import Event, EventContext
from palm.core.storage import StorageEngine
from bundles.standard.runtimes.mcp.assist.operator import (
    dispatch_operator_path,
    rewrite_system_session_continue,
)
from palm.system.subsystems.planes.session import SessionPlaneService, looks_like_system_session_id


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_event_matches_context_and_instance_attach() -> None:
    plane = SessionPlaneService(storage=_storage())
    bind = plane.bind(surface="test")
    sid = bind.session_id
    plane.attach_instance(sid, "inst-a")
    plane.attach_instance(sid, "inst-b")

    # Context attribution
    ev = Event(
        type="flow.session.succeeded",
        payload={"instance_id": "inst-a"},
        context=EventContext(session_id=sid, instance_id="inst-a"),
    )
    assert plane.event_matches(sid, event=ev)
    assert not plane.event_matches("sess-other", event=ev)

    # Payload system key
    assert plane.event_matches(
        sid, payload={"session_id": sid, "foo": 1}
    )

    # Reverse index via instance only
    assert plane.event_matches(sid, payload={"instance_id": "inst-b"})
    assert not plane.event_matches(sid, payload={"instance_id": "inst-foreign"})

    # make_event_filter
    filt = plane.make_event_filter(sid)
    assert filt(ev) is True
    foreign = Event(type="x", payload={"instance_id": "nope"})
    assert filt(foreign) is False


def test_resolve_continue_prefers_waiting_then_last() -> None:
    plane = SessionPlaneService(storage=_storage())
    sid = plane.bind().session_id
    plane.attach_instance(sid, "inst-1")
    plane.attach_instance(sid, "inst-2")
    # 0.58.10: new attach sets active → resolve returns active (inst-2)
    assert plane.resolve_continue_instance(sid) == "inst-2"
    plane.clear_active_instance(sid)
    # No active + no runtime waits → last attached
    assert plane.resolve_continue_instance(sid) == "inst-2"


def test_host_session_event_matches_and_continue() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="test")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-host-1")
        assert host.resolve_session_continue(bind.session_id) == "inst-host-1"
        ev = Event(
            type="resource.changed",
            payload={"instance_id": "inst-host-1"},
        )
        assert host.session_event_matches(bind.session_id, ev)
    finally:
        host.shutdown()


def test_rewrite_system_session_continue_path() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="test")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-continue")
        path, params = rewrite_system_session_continue(
            host,
            ["assist", "instance", bind.session_id, "input"],
            {"value": "hi"},
        )
        assert path[2] == "inst-continue"
        assert params["session_id"] == bind.session_id
        assert params["instance_id"] == "inst-continue"
        assert looks_like_system_session_id(params["session_id"])
    finally:
        host.shutdown()


def test_system_session_inspect_dispatch() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="test")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-inspect")
        journey = dispatch_operator_path(
            host, ["system", "session", bind.session_id], {}
        )
        assert journey["kind"] == "session_inspect"
        assert journey["session_id"] == bind.session_id
        assert "inst-inspect" in journey["instance_ids"]
        ids = dispatch_operator_path(
            host, ["system", "session", bind.session_id, "instances"], {}
        )
        assert ids == ["inst-inspect"]
    finally:
        host.shutdown()


def test_events_subscribe_session_filter_helper() -> None:
    """Unit-level: event filter used by Events WS (no full WS upgrade)."""
    from bundles.standard.runtimes.server.surfaces.websocket.events_session import (
        _event_matches_session,
    )

    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        bind = host.bind_session(surface="events")
        plane = host.session_plane
        assert plane is not None
        plane.attach_instance(bind.session_id, "inst-ev")
        ev_ok = Event(
            type="resource.changed",
            payload={"instance_id": "inst-ev"},
        )
        ev_no = Event(
            type="resource.changed",
            payload={"instance_id": "inst-other"},
        )
        assert _event_matches_session(host, bind.session_id, event=ev_ok)
        assert not _event_matches_session(host, bind.session_id, event=ev_no)
    finally:
        host.shutdown()


def test_workload_owner_enriched_from_event_context() -> None:
    from palm.core.workload import WorkloadSpec
    from palm.system.runtime.base import (
        _enrich_workload_owner_from_event_context,
    )
    from palm.core.workload.owner import WorkloadOwner

    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        rt = host.runtime()
        sid = host.bind_session(surface="wl").session_id
        with rt.event.bind_context(
            EventContext(session_id=sid, job_id="job-1", instance_id="inst-1")
        ):
            owner = _enrich_workload_owner_from_event_context(rt, WorkloadOwner())
        assert owner.session_id == sid
        assert owner.job_id == "job-1"
        assert owner.instance_id == "inst-1"
        # Spec smoke — engine may not start without runner; enrichment is the point
        del WorkloadSpec
    finally:
        host.shutdown()
