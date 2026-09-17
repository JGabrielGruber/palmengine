"""0.69.4 — palm.kits.present kit-as-composition.

Library door: one object holds one BoundSurface and walks bind, present,
submit, start, attach, focus. Not a PresentService. No pattern if.
Empty-handed guidance_definition_id / stamp caller: 0.69.5.
Title start still must not stamp when the definition id does not match.
"""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.common.job_inspection import JobContext
from palm.core.orchestration import JobStatus
from palm.core.wait import has_open_waits
from palm.services.session.bound_surface import BoundSurface
from palm.system.subsystems.planes.session.walk_writes import GUIDANCE_INSTANCE_ID
from tests.helpers.flows import spine_wizard

_ASSIST_ENVELOPE_KEYS = (
    "question",
    "handoff_ready",
    "inspect_catalog",
    "compose",
    "scenario_id",
    "operator_mode",
)


def test_present_kit_is_installed() -> None:
    import palm.kits.present as present
    from palm.kits import INSTALLED_KITS, get_kit, list_kits

    assert present is not None
    assert "present" in INSTALLED_KITS
    info = get_kit("present")
    assert info is not None
    assert info.module == "palm.kits.present"
    assert "present" in {k.name for k in list_kits()}


def test_bind_through_kit_returns_outside_bound_surface() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        surface = kit.bound

        assert isinstance(surface, BoundSurface)
        assert surface.kind == "outside"
        assert surface.session_id.startswith("sess-")
    finally:
        host.shutdown()


def test_present_waiting_run_via_job_inspectable_without_assist_envelope() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        kit.start(spine_wizard("chooser"), job_id="job-chooser")

        turn = kit.present()

        assert isinstance(turn, JobContext)
        assert turn.pattern == "wizard"
        payload = {k: getattr(turn, k) for k in turn.__dataclass_fields__}
        for key in _ASSIST_ENVELOPE_KEYS:
            assert key not in payload
        assert turn.waiting_on == () or isinstance(turn.waiting_on, tuple)
    finally:
        host.shutdown()


def test_submit_input_through_kit_uses_input_capable() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        kit.start(spine_wizard("title"), job_id="job-title")

        kit.submit("ok")

        job = host.runtime().orchestration.get_job("job-title")
        assert job.status == JobStatus.SUCCEEDED
    finally:
        host.shutdown()


def test_start_named_work_spawns_sibling_without_job_session() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        kit.start(spine_wizard("chooser"), job_id="job-chooser")
        parent_iid = kit.bound.instance_id
        assert parent_iid

        kit.start(spine_wizard("title"), job_id="job-title")
        child_iid = kit.bound.instance_id

        parent = host.runtime().orchestration.get_job("job-chooser")
        child = host.runtime().orchestration.get_job("job-title")
        svc = host.session

        assert parent.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (child.metadata or {})
        assert not has_open_waits(parent.state)
        owned = svc.list_instances(kit.bound.session_id)
        assert parent_iid in owned
        assert child_iid in owned
        assert GUIDANCE_INSTANCE_ID not in (kit.bound.metadata or {})
    finally:
        host.shutdown()


def test_focus_among_owned_instances() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        kit.start(spine_wizard("title-a"), job_id="job-a")
        iid_a = kit.bound.instance_id
        kit.start(spine_wizard("title-b"), job_id="job-b")
        iid_b = kit.bound.instance_id
        assert iid_a and iid_b and iid_a != iid_b
        assert host.session.active_instance(kit.bound.session_id) == iid_b

        surface = kit.focus(iid_a)

        assert surface.instance_id == iid_a
        assert kit.bound.instance_id == iid_a
        assert host.session.active_instance(kit.bound.session_id) == iid_a
    finally:
        host.shutdown()
