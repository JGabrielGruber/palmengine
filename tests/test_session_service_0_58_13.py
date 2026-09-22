"""0.58.13 — service / origin sessions for automated and host attribution (SI-011)."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.services.session import (
    HOST_SESSION_ID,
    WORK_DRAIN_ORIGIN,
    service_session_id,
)
from palm.system.subsystems.planes.session import service_session_id as plane_service_session_id


def _host() -> ApplicationHost:
    settings = PalmSettings(load_example_definitions=False)
    return ApplicationHost(
        settings=settings,
        profile=DeploymentProfile.all_in_one(),
        storage=StorageEngine(),
    )


def test_service_session_id_stable() -> None:
    assert service_session_id("host") == HOST_SESSION_ID
    assert service_session_id(WORK_DRAIN_ORIGIN) == "sess-svc-work-drain"
    assert service_session_id("work-drain:todo-analytics") == (
        "sess-svc-work-drain-todo-analytics"
    )
    assert service_session_id("work-drain:todo-analytics") == plane_service_session_id(
        "work-drain:todo-analytics"
    )


def test_host_session_exists_after_start() -> None:
    host = _host()
    host.start()
    try:
        rec = host.session.get(HOST_SESSION_ID)
        assert rec is not None
        assert rec.metadata.get("kind") == "service"
        assert rec.metadata.get("origin") == "host"
        # Idempotent
        assert host.session.ensure_host_session() == HOST_SESSION_ID
    finally:
        host.shutdown()


def test_ensure_service_session_stable_across_calls() -> None:
    host = _host()
    host.start()
    try:
        a = host.session.ensure_service_session("work-drain:demo")
        b = host.session.ensure_service_session("work-drain:demo")
        assert a == b == "sess-svc-work-drain-demo"
        rec = host.session.get(a)
        assert rec is not None
        assert rec.metadata.get("kind") == "service"
        assert rec.metadata.get("origin") == "work-drain:demo"
    finally:
        host.shutdown()


def test_enrich_submit_body_with_origin_uses_service_session() -> None:
    host = _host()
    host.start()
    try:
        body1 = host.session.enrich_submit_body(
            {"flow_name": "demo"},
            surface="work-drain",
            origin="work-drain:demo",
        )
        body2 = host.session.enrich_submit_body(
            {"flow_name": "demo"},
            surface="work-drain",
            origin="work-drain:demo",
        )
        sid1 = body1["metadata"]["session_id"]
        sid2 = body2["metadata"]["session_id"]
        assert sid1 == sid2 == "sess-svc-work-drain-demo"
        assert body1["metadata"].get("session_origin") == "work-drain:demo"
    finally:
        host.shutdown()


def test_enrich_without_origin_still_mints_outside_session() -> None:
    """Interactive / surface path: no origin → new outside subject each time."""
    host = _host()
    host.start()
    try:
        a = host.session.enrich_submit_body({"flow_name": "x"}, surface="execution")
        b = host.session.enrich_submit_body({"flow_name": "y"}, surface="execution")
        sa = a["metadata"]["session_id"]
        sb = b["metadata"]["session_id"]
        assert sa.startswith("sess-")
        assert sb.startswith("sess-")
        assert sa != sb
        assert not sa.startswith("sess-svc-")
    finally:
        host.shutdown()


def test_work_drain_submit_attributes_service_session() -> None:
    """Coordinator _submit enriches with work-drain:{target} before flow body."""
    host = _host()
    host.start()
    try:
        # Call the same path work drain uses without needing a real flow run:
        # exercise enrich policy that coordinator applies.
        session = host.session
        assert session is not None
        body = {
            "flow_name": "todo-analytics",
            "metadata": {"depth": 0},
        }
        origin = "work-drain:todo-analytics"
        enriched = session.enrich_submit_body(
            body, surface="work-drain", origin=origin
        )
        assert enriched["metadata"]["session_id"] == service_session_id(origin)

        # Second intent same target shares owner session
        again = session.enrich_submit_body(
            {"flow_name": "todo-analytics", "metadata": {}},
            surface="work-drain",
            origin=origin,
        )
        assert again["metadata"]["session_id"] == enriched["metadata"]["session_id"]
    finally:
        host.shutdown()
