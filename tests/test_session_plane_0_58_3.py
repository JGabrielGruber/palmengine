"""0.58.3 — Bind law: surfaces resolve/create system session on entry."""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from palm.system.subsystems.planes.session import (
    SessionBind,
    SessionClosedError,
    SessionNotFoundError,
    SessionPlaneError,
    SessionPlaneService,
    SessionStatus,
    require_session_plane,
)


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_bind_creates_system_session_without_id() -> None:
    plane = SessionPlaneService(storage=_storage())
    bind = plane.bind(surface="test")
    assert isinstance(bind, SessionBind)
    assert bind.created is True
    assert bind.session_id.startswith("sess-")
    assert bind.status == SessionStatus.OPEN
    assert bind.surface == "test"
    assert bind.instance_ids == ()
    rec = plane.require_open(bind.session_id)
    assert rec.metadata.get("surface") == "test"
    assert rec.metadata.get("last_surface") == "test"


def test_bind_reuses_existing_and_is_not_instance_alias() -> None:
    plane = SessionPlaneService(storage=_storage())
    first = plane.bind(surface="cli")
    again = plane.bind(first.session_id, surface="cli")
    assert again.created is False
    assert again.session_id == first.session_id
    # Bind result is never an instance-shaped product id
    assert again.session_id.startswith("sess-")
    assert again.session_id != "inst-whatever"


def test_bind_create_false_requires_id() -> None:
    plane = SessionPlaneService(storage=_storage())
    with pytest.raises(SessionPlaneError):
        plane.bind(create=False)
    with pytest.raises(SessionNotFoundError):
        plane.bind("sess-missing", create=False)


def test_bind_refuses_closed() -> None:
    plane = SessionPlaneService(storage=_storage())
    b = plane.bind(session_id="sess-closed-once", surface="test")
    plane.close(b.session_id)
    with pytest.raises(SessionClosedError):
        plane.bind("sess-closed-once", surface="test")
    with pytest.raises(SessionClosedError):
        plane.require_open("sess-closed-once")


def test_require_open_happy() -> None:
    plane = SessionPlaneService(storage=_storage())
    b = plane.bind()
    rec = plane.require_open(b.session_id)
    assert rec.session_id == b.session_id


def test_doctor_reports_bind_law() -> None:
    plane = SessionPlaneService(storage=_storage())
    snap = plane.doctor_snapshot()
    assert snap["bind_law"] is True
    assert "bind" in snap["verbs"]
    assert "require_open" in snap["verbs"]


def test_require_session_plane_helper() -> None:
    rt = EmbeddedRuntime()
    with pytest.raises(SessionPlaneError):
        require_session_plane(rt)
    rt.start()
    try:
        plane = require_session_plane(rt)
        bind = plane.bind(surface="embedded")
        assert bind.session_id.startswith("sess-")
    finally:
        rt.stop()
        clear_palm_runtime()


def test_host_bind_session() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    with pytest.raises(RuntimeError):
        host.bind_session(surface="test")
    host.start()
    try:
        assert host.session_plane is not None
        bind = host.bind_session(surface="host")
        assert bind.session_id.startswith("sess-")
        assert bind.created is True
        again = host.bind_session(bind.session_id, surface="host")
        assert again.created is False
        assert again.session_id == bind.session_id
        # distinct from any instance id
        assert host.session_plane.get(bind.session_id) is not None
    finally:
        host.shutdown()


def test_cli_context_bind_system_session_distinct_from_assist() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        ctx = CliContext(host=host, console=None)
        bind = ctx.bind_system_session(surface="cli")
        assert ctx.active_system_session_id == bind.session_id
        assert ctx.active_system_session_id.startswith("sess-")
        assert ctx.active_assist_session_id is None

        # Product assist may still pass instance-shaped session_id
        ctx.set_active_assist(
            {
                "instance_id": "inst-product-alias",
                "scenario_id": "demo",
                "refs": {"job_id": "job-1"},
            }
        )
        assert ctx.active_assist_session_id == "inst-product-alias"
        assert ctx.active_instance_id == "inst-product-alias"
        # System subject stays a real session (reused or still sess-*)
        assert ctx.active_system_session_id is not None
        assert ctx.active_system_session_id.startswith("sess-")
        assert ctx.active_system_session_id != ctx.active_assist_session_id

        # Explicit system session_id on view is honored
        other = host.bind_session(surface="cli")
        ctx.set_active_assist(
            {
                "session_id": other.session_id,
                "instance_id": "inst-other",
            }
        )
        assert ctx.active_system_session_id == other.session_id
        assert ctx.active_assist_session_id == "inst-other"
    finally:
        host.shutdown()


def test_set_active_binds_system_session() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        ctx = CliContext(host=host, console=None)
        ctx.set_active("inst-job-path", "job-abc")
        assert ctx.active_instance_id == "inst-job-path"
        assert ctx.active_system_session_id is not None
        assert ctx.active_system_session_id.startswith("sess-")
        assert ctx.active_system_session_id != "inst-job-path"
    finally:
        host.shutdown()
