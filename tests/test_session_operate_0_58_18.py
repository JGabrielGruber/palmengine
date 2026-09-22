"""0.58.18 — session operate + surface_view v2."""

from __future__ import annotations

from typing import Any

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from bundles.standard.runtimes.mcp.assist.operator import dispatch_operator_path
from palm.system.subsystems.planes.session import InstanceNotOwnedError, SessionPlaneError


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_focus_returns_bound_surface() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-a")
        svc.attach_instance(sid, "inst-b")
        bound = svc.focus(sid, "inst-a")
        assert bound.session_id == sid
        assert bound.instance_id == "inst-a"
        assert svc.active_instance(sid) == "inst-a"
        cleared = svc.clear_focus(sid)
        assert cleared.instance_id in ("inst-b", "inst-a", None) or cleared.session_id == sid
        # clear removes focus; resolve may fall back to last attached
        assert svc.active_instance(sid) is None
    finally:
        host.shutdown()


def test_focus_refuses_foreign_instance() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        a = svc.bind(surface="test").session_id
        b = svc.bind(surface="test").session_id
        svc.attach_instance(a, "owned")
        svc.attach_instance(b, "foreign")
        with pytest.raises(SessionPlaneError):
            svc.focus(a, "foreign")
    finally:
        host.shutdown()


def test_surface_view_v2_has_waiting_refs_actions() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind_surface(surface="test", origin="cli").session_id
        svc.attach_instance(sid, "inst-1")
        svc.focus(sid, "inst-1")
        view = svc.surface_view(sid)
        assert view["kind"] == "session_surface_view"
        assert view["view_version"] == 2
        assert view["session_kind"] == "outside"
        assert view["origin"] == "cli"
        assert view["continue_instance_id"] == "inst-1"
        assert "waiting" in view
        assert "waiting_on" in view
        assert view["refs"]["session_id"] == sid
        assert view["refs"]["instance_id"] == "inst-1"
        assert view["bound_surface"]["session_id"] == sid
        verbs = {a["verb"] for a in view["actions"]}
        assert "focus" in verbs
        assert "cancel_owned" in verbs
        assert "list_waiting" in verbs
        assert "surface_view" in verbs
        assert any(a.get("path", "").endswith("/view") for a in view["actions"])
    finally:
        host.shutdown()


def test_list_owned_waiting_alias() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-w")
        assert svc.list_owned_waiting(sid) == svc.list_waiting(sid)
    finally:
        host.shutdown()


def test_cancel_owned_gates_and_drives_system() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        other = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-own")
        svc.attach_instance(other, "inst-foreign")

        # Foreign instance refused before system cancel
        with pytest.raises(InstanceNotOwnedError):
            svc.cancel_owned(sid, instance_id="inst-foreign")

        # Stub system cancel + job resolution
        original_cancel = svc._inspect.cancel_job
        original_inspect = svc._inspect.inspect_instance
        calls: list[str] = []

        def _cancel(job_id: str, **kwargs: Any) -> dict[str, Any]:
            calls.append(job_id)
            return {"found": True, "job_id": job_id, "cancelled": True, "status": "CANCELLED"}

        def _inspect(instance_id: str) -> dict[str, Any]:
            if instance_id == "inst-own":
                return {"instance_id": "inst-own", "job_id": "job-own-1"}
            return {"instance_id": instance_id}

        svc._inspect.cancel_job = _cancel  # type: ignore[method-assign]
        svc._inspect.inspect_instance = _inspect  # type: ignore[method-assign]
        try:
            result = svc.cancel_owned(sid, instance_id="inst-own")
            assert result["kind"] == "session_cancel_owned"
            assert result["session_id"] == sid
            assert result["instance_id"] == "inst-own"
            assert result["job_id"] == "job-own-1"
            assert result["cancelled"] is True
            assert calls == ["job-own-1"]

            # Default target = continue focus
            calls.clear()
            svc.focus(sid, "inst-own")
            result2 = svc.cancel_owned(sid)
            assert result2["instance_id"] == "inst-own"
            assert calls == ["job-own-1"]
        finally:
            svc._inspect.cancel_job = original_cancel  # type: ignore[method-assign]
            svc._inspect.inspect_instance = original_inspect  # type: ignore[method-assign]
    finally:
        host.shutdown()


def test_cancel_owned_missing_job_is_honest() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-no-job")
        result = svc.cancel_owned(sid, instance_id="inst-no-job")
        assert result["found"] is False
        assert result["cancelled"] is False
        assert result["reason"] == "no_job_id_for_instance"
    finally:
        host.shutdown()


def test_operator_dispatch_focus_view_cancel() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "inst-x")
        svc.attach_instance(sid, "inst-y")

        view = dispatch_operator_path(host, ["system", "session", sid, "view"], {})
        assert view["view_version"] == 2
        assert view["kind"] == "session_surface_view"

        focused = dispatch_operator_path(
            host,
            ["system", "session", sid, "focus"],
            {"instance_id": "inst-x"},
        )
        assert focused["kind"] == "session_focus"
        assert focused["active_instance_id"] == "inst-x"
        assert svc.active_instance(sid) == "inst-x"

        cleared = dispatch_operator_path(
            host, ["system", "session", sid, "focus", "clear"], {}
        )
        assert cleared["kind"] == "session_focus_clear"
        assert svc.active_instance(sid) is None

        # cancel without job → honest missing
        cancelled = dispatch_operator_path(
            host,
            ["system", "session", sid, "cancel"],
            {"instance_id": "inst-x"},
        )
        assert cancelled["kind"] == "session_cancel_owned"
        assert cancelled["instance_id"] == "inst-x"
    finally:
        host.shutdown()


def test_operator_cancel_all_owned() -> None:
    host = _host()
    host.start()
    try:
        svc = host.session
        sid = svc.bind(surface="test").session_id
        svc.attach_instance(sid, "a")
        svc.attach_instance(sid, "b")

        def _inspect(instance_id: str) -> dict[str, Any]:
            return {"instance_id": instance_id, "job_id": f"job-{instance_id}"}

        def _cancel(job_id: str, **kwargs: Any) -> dict[str, Any]:
            return {"found": True, "job_id": job_id, "cancelled": True, "status": "CANCELLED"}

        svc._inspect.inspect_instance = _inspect  # type: ignore[method-assign]
        svc._inspect.cancel_job = _cancel  # type: ignore[method-assign]

        out = dispatch_operator_path(
            host, ["system", "session", sid, "cancel", "all"], {}
        )
        assert out["kind"] == "session_cancel_all_owned"
        assert out["count"] == 2
        assert out["cancelled_count"] == 2
    finally:
        host.shutdown()
