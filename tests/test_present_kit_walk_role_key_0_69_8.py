"""0.69.8 — present kit owns the walk-role key; session walk-write stays generic.

Session stores the pointer as named metadata. The kit owns the key string
and the stamp/replace callers. Session verbs do not say guidance.
"""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from palm.core.orchestration import JobStatus
from plugins.kits import present
from palm.services.session.bound_surface import SESSION_CONTEXT_KEYS
from palm.services.session.service import SessionService
from palm.system.subsystems.planes.session import SessionPlaneService, walk_writes
from tests.helpers.flows import spine_wizard


def test_present_kit_owns_walk_role_key_constant() -> None:
    assert present.GUIDANCE_INSTANCE_ID == "guidance_instance_id"
    assert not hasattr(walk_writes, "GUIDANCE_INSTANCE_ID")


def test_session_service_and_plane_have_no_guidance_verbs() -> None:
    assert not hasattr(SessionService, "stamp_guidance_instance")
    assert not hasattr(SessionService, "replace_guidance_instance")
    assert not hasattr(SessionPlaneService, "stamp_guidance_instance")
    assert not hasattr(SessionPlaneService, "replace_guidance_instance")


def test_bound_surface_session_context_keys_omit_kit_role() -> None:
    assert "guidance_instance_id" not in SESSION_CONTEXT_KEYS


def test_empty_handed_start_stamps_session_metadata_under_kit_key() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        guide = spine_wizard("guide-chooser")
        host.runtime().repository.register_flow(guide)
        kit = present.bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = guide.definition_id

        surface = kit.start()
        iid = surface.instance_id
        assert iid
        inst = host.runtime().get_instance(iid)
        job = host.runtime().get_job(inst.job_id)
        assert job.status == JobStatus.WAITING_FOR_INPUT
        assert kit.bound.metadata[present.GUIDANCE_INSTANCE_ID] == iid
        assert host.session.get_metadata(kit.bound.session_id)[
            present.GUIDANCE_INSTANCE_ID
        ] == iid
        assert "session_id" not in (job.metadata or {})
    finally:
        host.shutdown()
