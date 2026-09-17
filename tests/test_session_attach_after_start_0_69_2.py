"""0.69.2 — session-side attach after start. Job stays session-ignorant.

Floor glue: after execution start, SessionService attaches the new instance
on the bound session. Do not copy session_id onto the job.
Attach is geometry — it does not stamp guidance_instance_id.
Kit start() is a later slice.
"""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.system.subsystems.planes.session.walk_writes import GUIDANCE_INSTANCE_ID
from tests.helpers.flows import spine_wizard


def _start_without_job_session(host: ApplicationHost, name: str):
    job = host.submit_flow(spine_wizard(name), job_id=f"job-{name}")
    iid = str(job.metadata.get("instance_id") or "")
    assert iid
    return job, iid


def test_bind_start_without_job_session_then_session_side_attach() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        job, iid = _start_without_job_session(host, "title-a")

        assert "session_id" not in (job.metadata or {})
        assert not svc.owns_instance(bound.session_id, iid)

        surface = svc.attach_after_start(bound.session_id, iid)

        assert svc.owns_instance(bound.session_id, iid)
        assert "session_id" not in (job.metadata or {})
        assert surface.session_id == bound.session_id
        assert iid in svc.list_instances(bound.session_id)
    finally:
        host.shutdown()


def test_second_start_attaches_as_sibling_and_steals_continue_focus() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        _job_a, iid_a = _start_without_job_session(host, "title-a")
        svc.attach_after_start(bound.session_id, iid_a)

        _job_b, iid_b = _start_without_job_session(host, "title-b")
        svc.attach_after_start(bound.session_id, iid_b)

        owned = svc.list_instances(bound.session_id)
        assert iid_a in owned
        assert iid_b in owned
        assert svc.owns_instance(bound.session_id, iid_a)
        assert svc.active_instance(bound.session_id) == iid_b
    finally:
        host.shutdown()


def test_attach_after_start_does_not_stamp_guidance_instance_id() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        _job, iid = _start_without_job_session(host, "title-a")

        surface = svc.attach_after_start(bound.session_id, iid)

        assert GUIDANCE_INSTANCE_ID not in (surface.metadata or {})
        assert GUIDANCE_INSTANCE_ID not in svc.get_metadata(bound.session_id)
    finally:
        host.shutdown()


def test_start_without_session_side_attach_does_not_own_via_job_metadata() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        job, iid = _start_without_job_session(host, "orphan")

        assert "session_id" not in (job.metadata or {})
        assert not svc.owns_instance(bound.session_id, iid)
        assert svc.owner_session_id(iid) is None
    finally:
        host.shutdown()
