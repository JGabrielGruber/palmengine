"""0.58.17 — single kit door + BoundSurface dogfood (no product plane dual-path)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from plugins.kits.server.middleware import (
    require_session_service,
    resolve_session_plane,
    resolve_session_service,
)
from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.mcp.assist.operator import (
    dispatch_system,
    rewrite_system_session_continue,
)
from bundles.standard.runtimes.server.surfaces.websocket.session import (
    _ConnectionState,
    _service_bind_into,
    handle_client_message,
)
from palm.services.session import BoundSurface, SessionService
from palm.system.subsystems.planes.session import InstanceNotOwnedError


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_resolve_session_service_from_host_and_ctx() -> None:
    host = _host()
    host.start()
    try:
        assert resolve_session_service(host) is host.session
        assert isinstance(resolve_session_service(host), SessionService)
        ctx = SimpleNamespace(session=host.session, host=host)
        assert resolve_session_service(ctx) is host.session
        nested = SimpleNamespace(host=host)
        assert resolve_session_service(nested) is host.session
        assert require_session_service(ctx) is host.session
        # Product door does not fall back to raw plane via this helper
        plane_only = SimpleNamespace(session_plane=host.session_plane)
        assert resolve_session_service(plane_only) is None
        assert resolve_session_plane(plane_only) is host.session_plane
    finally:
        host.shutdown()


def test_require_session_service_raises_when_missing() -> None:
    with pytest.raises(RuntimeError, match="SessionService not available"):
        require_session_service(SimpleNamespace())


def test_rewrite_uses_product_door_only_no_plane_fallback() -> None:
    host = _host()
    host.start()
    try:
        sid = host.session.bind(surface="test").session_id
        host.session.attach_instance(sid, "inst-a")
        host.session.set_active_instance(sid, "inst-a")

        # Service present → rewrite works
        ctx = SimpleNamespace(session=host.session, host=host)
        path, params = rewrite_system_session_continue(
            ctx, ["assist", "instance", sid], {}
        )
        assert path[2] == "inst-a"
        assert params["session_id"] == sid

        # Plane only (no product door) → no rewrite (0.58.17: no dual path)
        plane_ctx = SimpleNamespace(session_plane=host.session_plane)
        path2, params2 = rewrite_system_session_continue(
            plane_ctx, ["assist", "instance", sid], {}
        )
        assert path2[2] == sid  # untouched system id still in path
        assert "instance_id" not in params2
    finally:
        host.shutdown()


def test_dispatch_system_session_requires_product_door() -> None:
    host = _host()
    host.start()
    try:
        sid = host.session.bind(surface="test").session_id
        host.session.attach_instance(sid, "i1")
        ctx = SimpleNamespace(
            session=host.session,
            host=host,
            system=host.system,
            runtime=host.runtime(),
        )
        view = dispatch_system(ctx, ["system", "session", sid], {})
        assert view["session_id"] == sid
        assert "i1" in view.get("instance_ids", [])

        with pytest.raises(ValueError, match="SessionService not available"):
            dispatch_system(
                SimpleNamespace(session_plane=host.session_plane, system=host.system),
                ["system", "session", sid],
                {},
            )
    finally:
        host.shutdown()


def test_ws_bind_uses_session_service_and_bound_surface() -> None:
    host = _host()
    host.start()
    try:
        ctx = SimpleNamespace(session=host.session, host=host)
        conn = _ConnectionState(headers={})
        _service_bind_into(conn, None, ctx=ctx, create=True)
        assert conn.session_id and conn.session_id.startswith("sess-")
        assert isinstance(conn.bound, BoundSurface)
        assert conn.bound.session_id == conn.session_id
        assert conn.bound.kind == "outside"
        assert conn.bound.origin == "websocket"
        snap = conn.bound_snapshot()
        assert snap["session_id"] == conn.session_id
        assert snap["bound_surface"]["session_id"] == conn.session_id

        # Re-bind same id via op:bind
        frame = handle_client_message(
            {"op": "bind", "session_id": conn.session_id, "id": 1},
            ctx=ctx,
            conn=conn,
        )
        assert frame is not None
        assert frame["op"] == "bound"
        assert frame["session_id"] == conn.session_id
        assert frame.get("bound_surface")
        assert frame["created"] is False
    finally:
        host.shutdown()


def test_cli_context_binds_bound_surface() -> None:
    host = _host()
    host.start()
    try:
        cli = CliContext(host=host, console=None)
        result = cli.bind_system_session(surface="cli")
        assert isinstance(cli.bound_surface, BoundSurface)
        assert cli.active_system_session_id == cli.bound_surface.session_id
        assert cli.bound_surface.origin == "cli"
        assert cli.bound_surface.kind == "outside"
        # Result is BoundSurface when product door present
        assert isinstance(result, BoundSurface)

        # Assist envelope updates instance on BoundSurface
        iid = "inst-cli-1"
        host.session.attach_instance(cli.bound_surface.session_id, iid)
        cli.set_active_assist(
            {
                "session_id": cli.bound_surface.session_id,
                "instance_id": iid,
                "refs": {"job_id": "job-1"},
            }
        )
        assert cli.active_instance_id == iid
        assert cli.bound_surface.instance_id == iid
        assert cli.active_system_session_id == cli.bound_surface.session_id
    finally:
        host.shutdown()


def test_ws_gate_still_enforced_via_product_door() -> None:
    host = _host()
    host.start()
    try:
        a = host.session.bind(surface="test").session_id
        b = host.session.bind(surface="test").session_id
        host.session.attach_instance(a, "owned")
        host.session.attach_instance(b, "foreign")
        ctx = SimpleNamespace(session=host.session, host=host)
        with pytest.raises(InstanceNotOwnedError):
            rewrite_system_session_continue(
                ctx,
                ["assist", "instance", "foreign"],
                {"session_id": a},
            )
    finally:
        host.shutdown()
