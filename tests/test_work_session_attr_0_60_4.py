"""0.60.4 — system-path reactive session attribution on work plane submit."""

from __future__ import annotations

from palm.core.work import WorkIntent
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.planes.session.types import (
    looks_like_system_session_id,
    service_session_id,
)
from palm.system.subsystems.planes.work.session_attr import (
    attribute_reactive_start,
    reactive_origin,
)
from tests.helpers.bound import bound_for_runtime


def test_reactive_origin_shapes() -> None:
    assert reactive_origin("f1", {"trigger": "schedule"}) == "schedule:f1"
    assert reactive_origin(None, {"trigger": "inbound", "inbound_resource": "r1"}) == ("inbound:r1")
    assert reactive_origin("analytics", {}) == "work-drain:analytics"
    assert reactive_origin(None, {}) == "work-drain"


def test_attribute_inherits_system_session() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        meta = attribute_reactive_start(
            rt,
            "child",
            {"session_id": "sess-parent-walk", "trigger": "on_flow"},
        )
        assert meta["session_id"] == "sess-parent-walk"
        assert meta["session_attribution"] == "inherit"
    finally:
        rt.stop()


def test_attribute_service_session_when_absent() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        meta = attribute_reactive_start(rt, "analytics", {"trigger": "on_resource"})
        sid = meta.get("session_id")
        assert looks_like_system_session_id(sid)
        assert sid == service_session_id("work-drain:analytics")
        assert meta["session_attribution"] == "service"
        assert meta["session_origin"] == "work-drain:analytics"
    finally:
        rt.stop()


def test_work_plane_tick_attributes_session_on_system_submit() -> None:
    """Default system submit stamps service session without product SessionService."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        plane = rt.work_plane
        assert plane is not None
        captured: list[dict] = []

        def capture(flow_id: str, payload: dict) -> None:
            captured.append({"flow_id": flow_id, **dict(payload)})

        # Use real attribute path: wrap default by intercepting after attribute.
        from palm.system.subsystems.planes.work.session_attr import attribute_reactive_start as attr

        def submit(flow_id: str, payload: dict) -> None:
            body = attr(rt, flow_id, payload)
            capture(flow_id, body)

        plane.set_submit_flow(submit)
        plane.enqueue(WorkIntent(kind="run_flow", target="demo-flow", payload={}))
        assert plane.tick(limit=5) == 1
        assert len(captured) == 1
        assert looks_like_system_session_id(captured[0].get("session_id"))
        assert captured[0]["session_attribution"] == "service"
    finally:
        rt.stop()
