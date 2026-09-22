"""0.58.7 / 0.58.9 — WS / cookie-like bind; session_id = system subject."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from plugins.kits.server.middleware import (
    PALM_SESSION_COOKIE,
    PALM_SESSION_HEADER,
    extract_system_session_hint,
    parse_cookie_header,
    resolve_session_plane,
    set_cookie_header_value,
)
from bundles.standard.runtimes.server.surfaces.websocket.session import (
    _ConnectionState,
    handle_client_message,
)
from palm.system.subsystems.planes.session import looks_like_system_session_id


def test_looks_like_system_session_id() -> None:
    assert looks_like_system_session_id("sess-abc")
    assert not looks_like_system_session_id("inst-abc")
    assert not looks_like_system_session_id("")
    assert not looks_like_system_session_id(None)


def test_cookie_header_parse_and_hint() -> None:
    assert parse_cookie_header("a=1; palm_session=sess-from-cookie; b=2")[
        PALM_SESSION_COOKIE
    ] == "sess-from-cookie"
    assert (
        extract_system_session_hint(
            {PALM_SESSION_HEADER: "sess-header", "Cookie": "palm_session=sess-cookie"}
        )
        == "sess-header"
    )
    assert (
        extract_system_session_hint({"Cookie": "palm_session=sess-cookie-only"})
        == "sess-cookie-only"
    )
    assert extract_system_session_hint({}) is None
    cookie = set_cookie_header_value("sess-xyz")
    assert cookie.startswith(f"{PALM_SESSION_COOKIE}=sess-xyz")
    assert "HttpOnly" in cookie


def test_ws_bind_creates_system_session_on_plane() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        conn = _ConnectionState(headers={})
        bound = handle_client_message(
            {"op": "bind", "id": "b1"},
            ctx=host,
            conn=conn,
        )
        assert bound is not None
        assert bound["op"] == "bound"
        sid = bound["session_id"]
        assert sid and looks_like_system_session_id(sid)
        assert conn.session_id == sid
        assert bound.get("created") is True
        plane = host.session_plane
        assert plane is not None
        rec = plane.require_open(sid)
        assert rec.session_id == sid

        again = handle_client_message(
            {"op": "bind", "id": "b2", "session_id": sid},
            ctx=host,
            conn=conn,
        )
        assert again is not None
        assert again["session_id"] == sid
        assert again.get("created") is False
    finally:
        host.shutdown()


def test_ws_bind_product_instance_stays_separate_from_system() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        conn = _ConnectionState(headers={})
        bound = handle_client_message(
            {
                "op": "bind",
                "id": "b1",
                "instance_id": "inst-product",
                "flow_id": "todo-builder",
            },
            ctx=host,
            conn=conn,
        )
        assert bound is not None
        assert bound["instance_id"] == "inst-product"
        assert bound["flow_id"] == "todo-builder"
        assert bound["session_id"] != "inst-product"
        assert looks_like_system_session_id(bound["session_id"])
        assert conn.instance_id == "inst-product"
        assert conn.session_id == bound["session_id"]
    finally:
        host.shutdown()


def test_ws_bind_sess_shaped_session_id_is_system() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        conn = _ConnectionState(headers={})
        bound = handle_client_message(
            {"op": "bind", "id": "b1", "session_id": "sess-explicit-ws"},
            ctx=host,
            conn=conn,
        )
        assert bound is not None
        assert bound["session_id"] == "sess-explicit-ws"
        assert conn.session_id == "sess-explicit-ws"
        assert conn.instance_id is None
        plane = host.session_plane
        assert plane is not None
        assert plane.get("sess-explicit-ws") is not None
    finally:
        host.shutdown()


def test_ws_cookie_header_binds_on_hello() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        plane = host.session_plane
        assert plane is not None
        plane.open(session_id="sess-cookie-hello")

        conn = _ConnectionState(
            headers={"Cookie": "palm_session=sess-cookie-hello"}
        )
        hello = handle_client_message(
            {"op": "hello", "id": "h1", "client": "portal"},
            ctx=host,
            conn=conn,
        )
        assert hello is not None
        assert hello["op"] == "hello"
        assert hello["bound"]["session_id"] == "sess-cookie-hello"
        assert conn.session_id == "sess-cookie-hello"
    finally:
        host.shutdown()


def test_ws_bind_refuses_closed_system_session() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        plane = host.session_plane
        assert plane is not None
        plane.open(session_id="sess-closed-ws")
        plane.close("sess-closed-ws")
        conn = _ConnectionState(headers={})
        err = handle_client_message(
            {"op": "bind", "id": "b1", "session_id": "sess-closed-ws"},
            ctx=host,
            conn=conn,
        )
        assert err is not None
        assert err["op"] == "error"
        assert err["error"]["code"] == "session_closed"
    finally:
        host.shutdown()


def test_resolve_session_plane_from_host() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        plane = resolve_session_plane(host)
        assert plane is host.session_plane
        assert plane is not None
    finally:
        host.shutdown()


def test_ws_dispatch_injects_session_id() -> None:
    """Dispatch without explicit session still binds and exposes system subject."""
    settings = PalmSettings.for_tests(load_examples=True)
    host = ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
    )
    host.start()
    try:
        conn = _ConnectionState(headers={})
        frame = handle_client_message(
            {"op": "dispatch", "id": "d1", "alias": "assist/doctor"},
            ctx=host,
            conn=conn,
        )
        assert frame is not None
        assert frame["op"] == "turn"
        bound = frame.get("bound") or {}
        assert looks_like_system_session_id(bound.get("session_id"))
        assert conn.session_id == bound["session_id"]
    finally:
        host.shutdown()
