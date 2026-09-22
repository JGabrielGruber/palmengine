"""0.58.14 — BoundSurface + session context metadata (session owns surface context)."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.services.session import (
    HOST_SESSION_ID,
    BoundSurface,
    SessionService,
    derive_session_kind,
    derive_session_origin,
)
from palm.system.subsystems.planes.session import SessionClosedError


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_bound_surface_requires_system_session_id() -> None:
    with pytest.raises(ValueError):
        BoundSurface(session_id="inst-not-system")
    with pytest.raises(ValueError):
        BoundSurface(session_id="")


def test_derive_kind_host_service_outside() -> None:
    assert derive_session_kind(HOST_SESSION_ID, {"kind": "service", "origin": "host"}) == (
        "host"
    )
    assert derive_session_kind("sess-svc-work-drain", {"kind": "service"}) == "service"
    assert derive_session_kind("sess-abc", {}) == "outside"
    assert derive_session_kind("sess-abc", {"kind": "outside"}) == "outside"
    assert derive_session_origin(HOST_SESSION_ID, {}) == "host"
    assert derive_session_origin("sess-x", {"origin": "mcp"}) == "mcp"


def test_bind_surface_returns_outside_bound_surface() -> None:
    host = _host()
    host.start()
    try:
        svc: SessionService = host.session
        bound = svc.bind_surface(surface="cli", origin="cli")
        assert isinstance(bound, BoundSurface)
        assert bound.session_id.startswith("sess-")
        assert not bound.session_id.startswith("sess-svc-")
        assert bound.kind == "outside"
        assert bound.origin == "cli"
        assert bound.metadata.get("kind") == "outside"
        assert bound.metadata.get("last_surface") == "cli"
        assert bound.instance_id is None
    finally:
        host.shutdown()


def test_bind_surface_with_instance_and_resolve() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-1")
        svc.attach_instance(sid, "inst-2")
        svc.set_active_instance(sid, "inst-1")

        bound = svc.bind_surface(sid, surface="test")
        assert bound.session_id == sid
        assert bound.instance_id == "inst-1"

        bound2 = svc.surface_from_session(sid, instance_id="inst-2")
        assert bound2.instance_id == "inst-2"
    finally:
        host.shutdown()


def test_session_metadata_merge_roundtrip() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="mcp", origin="mcp")
        sid = bound.session_id

        updated = svc.merge_metadata(
            sid,
            {"labels": {"agent": "grok"}, "walk": "design", "prefs": {"theme": "dark"}},
        )
        assert updated.metadata["labels"] == {"agent": "grok"}
        assert updated.metadata["walk"] == "design"
        assert updated.metadata.get("kind") == "outside"  # preserved
        assert updated.metadata.get("origin") == "mcp"

        got = svc.get_metadata(sid)
        assert got["walk"] == "design"
        assert got["prefs"] == {"theme": "dark"}

        # Plane door matches product
        plane_meta = svc.plane().get_metadata(sid)
        assert plane_meta["walk"] == "design"
    finally:
        host.shutdown()


def test_replace_metadata_does_not_touch_attach_list() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind_surface(surface="t").session_id
        svc.attach_instance(sid, "i1")
        replaced = svc.replace_metadata(sid, {"kind": "outside", "origin": "reset"})
        assert replaced.metadata == {"kind": "outside", "origin": "reset"}
        assert svc.list_instances(sid) == ["i1"]
        assert svc.active_instance(sid) == "i1"
    finally:
        host.shutdown()


def test_surface_from_params_create_and_existing() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        assert svc.surface_from_params({}) is None
        created = svc.surface_from_params(
            {"origin": "mcp"},
            create=True,
            surface="mcp",
        )
        assert created is not None
        assert created.kind == "outside"
        assert created.origin == "mcp"

        again = svc.surface_from_params(
            {"session_id": created.session_id, "instance_id": None}
        )
        assert again is not None
        assert again.session_id == created.session_id
    finally:
        host.shutdown()


def test_host_and_service_bound_surface_kinds() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        host_bound = svc.surface_from_session(HOST_SESSION_ID)
        assert host_bound.kind == "host"
        assert host_bound.origin == "host"

        sid = svc.ensure_service_session("work-drain:demo")
        assert sid is not None
        svc_bound = svc.surface_from_session(sid)
        assert svc_bound.kind == "service"
        assert svc_bound.origin == "work-drain:demo"
    finally:
        host.shutdown()


def test_surface_view_includes_bound_surface() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="test", origin="test")
        svc.attach_instance(bound.session_id, "inst-1")
        view = svc.surface_view(bound.session_id)
        assert view["kind"] == "session_surface_view"
        assert view["session_kind"] == "outside"
        assert view["origin"] == "test"
        assert view["bound_surface"]["session_id"] == bound.session_id
        assert view["bound_surface"]["session_kind"] == "outside"
        assert view["continue_instance_id"] == "inst-1"
        assert view["bound_surface"]["instance_id"] == "inst-1"
    finally:
        host.shutdown()


def test_bound_surface_to_dict_roundtrip() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="cli", metadata={"labels": {"a": 1}})
        data = bound.to_dict()
        assert data["kind"] == "bound_surface"
        rebuilt = BoundSurface.from_dict(data)
        assert rebuilt.session_id == bound.session_id
        assert rebuilt.metadata.get("labels") == {"a": 1}
        live = svc.surface_from_dict(data)
        assert live.session_id == bound.session_id
    finally:
        host.shutdown()


def test_merge_metadata_refuses_closed() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind_surface().session_id
        svc.close(sid)
        with pytest.raises(SessionClosedError):
            svc.merge_metadata(sid, {"walk": "nope"})
    finally:
        host.shutdown()


def test_session_metadata_not_job_blackboard() -> None:
    """Session meta holds walk facts; job path would use instance meta separately."""
    host = _host()
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(
            surface="mcp",
            metadata={"walk": "assist/discover", "client": "agent"},
        )
        # These must not require a job to exist
        meta = svc.get_metadata(bound.session_id)
        assert meta["walk"] == "assist/discover"
        assert meta["client"] == "agent"
        # Attaching an instance does not move session meta onto "job"
        svc.attach_instance(bound.session_id, "inst-x")
        still = svc.get_metadata(bound.session_id)
        assert still["walk"] == "assist/discover"
    finally:
        host.shutdown()
