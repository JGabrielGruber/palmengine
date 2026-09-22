"""0.69.5 — kit-contributed guidance_definition_id + stamp caller + replace.

Present kit owns ``guidance_definition_id`` (str | None). Unset → no
empty-handed start. Stamp after session-side attach iff the started
definition id equals that key. Replace only when the instance is already
attached and its definition id equals. Titles cannot become Home.
"""

from __future__ import annotations

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from palm.core.orchestration import JobStatus
from plugins.kits.present import GUIDANCE_INSTANCE_ID
from palm.system.subsystems.planes.session import InstanceNotOwnedError
from tests.helpers.flows import spine_wizard


def test_unset_guidance_definition_id_refuses_empty_handed_start() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        kit = bind(host, surface="embedded", origin="test")
        sid = kit.bound.session_id

        assert kit.guidance_definition_id is None
        with pytest.raises(RuntimeError, match="guidance_definition_id"):
            kit.start()

        assert kit.bound.instance_id is None
        assert host.session.list_instances(sid) == []
        jobs = host.runtime().orchestration.list_jobs()
        assert jobs == [] or all(
            getattr(j, "name", None) != "operator-entry" for j in jobs
        )
    finally:
        host.shutdown()


def test_empty_handed_start_uses_kit_guidance_definition_and_stamps() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        guide = spine_wizard("guide-chooser")
        host.runtime().repository.register_flow(guide)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = guide.definition_id

        surface = kit.start()

        iid = surface.instance_id
        assert iid
        inst = host.runtime().get_instance(iid)
        assert inst.flow_id == guide.definition_id
        job = host.runtime().get_job(inst.job_id)
        assert job.status == JobStatus.WAITING_FOR_INPUT
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == iid
        assert "session_id" not in (job.metadata or {})
    finally:
        host.shutdown()


def test_start_of_guidance_definition_stamps_if_absent() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        guide = spine_wizard("guide-chooser")
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = guide.definition_id

        kit.start(guide, job_id="job-guide")

        iid = kit.bound.instance_id
        assert iid
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == iid
    finally:
        host.shutdown()


def test_start_of_title_does_not_stamp_or_replace_home() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        guide = spine_wizard("guide-chooser")
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = guide.definition_id
        kit.start(guide, job_id="job-guide")
        home = kit.bound.instance_id
        assert home
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home

        kit.start(spine_wizard("title"), job_id="job-title")
        title = kit.bound.instance_id
        assert title and title != home

        owned = host.session.list_instances(kit.bound.session_id)
        assert home in owned
        assert title in owned
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home
    finally:
        host.shutdown()


def test_replace_only_when_attached_and_definition_id_equals() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        guide = spine_wizard("guide-chooser")
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = guide.definition_id
        kit.start(guide, job_id="job-guide-1")
        first = kit.bound.instance_id
        kit.start(guide, job_id="job-guide-2")
        second = kit.bound.instance_id
        kit.start(spine_wizard("title"), job_id="job-title")
        title = kit.bound.instance_id
        assert first and second and title
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == first

        with pytest.raises(InstanceNotOwnedError):
            kit.replace_guidance_instance("inst-foreign")
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == first

        with pytest.raises(ValueError, match="guidance_definition_id"):
            kit.replace_guidance_instance(title)
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == first

        surface = kit.replace_guidance_instance(second)
        assert surface.metadata[GUIDANCE_INSTANCE_ID] == second
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == second
    finally:
        host.shutdown()


def test_attach_focus_and_raw_start_without_kit_do_not_stamp() -> None:
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        job = host.submit_flow(spine_wizard("chooser"), job_id="job-raw")
        iid = str(job.metadata.get("instance_id") or "")
        assert iid
        attached = svc.attach_after_start(bound.session_id, iid)
        focused = svc.focus(bound.session_id, iid)

        assert GUIDANCE_INSTANCE_ID not in (attached.metadata or {})
        assert GUIDANCE_INSTANCE_ID not in (focused.metadata or {})

        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = spine_wizard("guide-chooser").definition_id
        raw = host.execution.flows.spawn_sibling(
            kit.bound.session_id,
            spine_wizard("guide-chooser"),
            job_id="job-raw-sibling",
        )
        assert GUIDANCE_INSTANCE_ID not in (raw.metadata or {})
        assert GUIDANCE_INSTANCE_ID not in (kit.bound.metadata or {})
    finally:
        host.shutdown()
