"""Portal dogfood — session vs instance slots (not a 0.68 compost slice)."""

from __future__ import annotations

from pathlib import Path

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.server.surfaces.websocket.session import (
    _ConnectionState,
    handle_client_message,
)
from palm.system.subsystems.planes.session import looks_like_system_session_id

PORTAL_JS = (
    Path(__file__).resolve().parents[1]
    / "src/palm/runtimes/server/surfaces/websocket/static/portal.js"
)


def test_portal_js_keeps_two_slots_and_honest_clear() -> None:
    source = PORTAL_JS.read_text(encoding="utf-8")
    assert "instanceId: null" in source
    assert "clear: true" in source
    assert "payload.instance_id && !state.sessionId" not in source
    assert "!state.bootstrapped && !state.sessionId" not in source
    assert "if (!state.bootstrapped)" in source
    assert "withContinueParams" in source


def test_bind_null_session_clears_instance_without_sticky() -> None:
    conn = _ConnectionState(headers={})
    conn.session_id = "sess-keep"
    conn.instance_id = "inst-old"
    bound = handle_client_message(
        {"op": "bind", "id": "c1", "session_id": None},
        conn=conn,
    )
    assert bound is not None
    assert bound["op"] == "bound"
    assert bound["session_id"] is None
    assert bound["instance_id"] is None
    assert conn.session_id is None
    assert conn.instance_id is None


def test_bind_clear_true_drops_both_slots() -> None:
    conn = _ConnectionState(headers={})
    conn.session_id = "sess-keep"
    conn.instance_id = "inst-old"
    conn.flow_id = "todo-builder"
    bound = handle_client_message(
        {
            "op": "bind",
            "id": "c1",
            "clear": True,
            "session_id": None,
            "instance_id": None,
            "flow_id": None,
        },
        conn=conn,
    )
    assert bound is not None
    assert bound["session_id"] is None
    assert bound["instance_id"] is None
    assert bound["flow_id"] is None
    assert conn.bound is None


def test_portal_shaped_menu_clear_does_not_inject_previous_instance() -> None:
    settings = PalmSettings.for_tests(load_examples=True)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    try:
        conn = _ConnectionState(headers={})
        first = handle_client_message(
            {
                "op": "bind",
                "id": "b1",
                "instance_id": "inst-sticky",
                "flow_id": "todo-builder",
            },
            ctx=host,
            conn=conn,
        )
        assert first is not None
        assert first["instance_id"] == "inst-sticky"
        assert looks_like_system_session_id(first["session_id"])

        cleared = handle_client_message(
            {
                "op": "bind",
                "id": "b2",
                "clear": True,
                "session_id": None,
                "instance_id": None,
            },
            ctx=host,
            conn=conn,
        )
        assert cleared is not None
        assert conn.instance_id is None
        assert conn.session_id is None

        frame = handle_client_message(
            {
                "op": "dispatch",
                "id": "d1",
                "alias": "assist/menu",
                "format": "assistant",
                "params": {},
            },
            ctx=host,
            conn=conn,
        )
        assert frame is not None
        assert frame["op"] == "turn"
        assert conn.instance_id != "inst-sticky"
        payload = frame.get("payload") or {}
        path = payload.get("path") or []
        assert "inst-sticky" not in [str(p) for p in path]
        bound = frame.get("bound") or {}
        assert bound.get("instance_id") != "inst-sticky"
    finally:
        host.shutdown()
