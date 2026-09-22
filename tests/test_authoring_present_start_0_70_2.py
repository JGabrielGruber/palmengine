"""0.70.2 — present starts the committed catalog definition.

Remaining Authoring floor: land/commit on embedded definitions, then
plugins.kits.present starts that catalog id on the same host.

Not land verbs on present. Not a leftover in-memory FlowDefinition.
Handle classes stay unnamed.
"""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from palm.common.job_inspection import JobContext
from palm.core.orchestration import JobStatus
from palm.definitions.flow import FlowDefinition
from plugins.kits.present import GUIDANCE_INSTANCE_ID


def _wizard_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


_ASSIST_ENVELOPE_KEYS = (
    "question",
    "handoff_ready",
    "inspect_catalog",
    "compose",
    "scenario_id",
    "operator_mode",
)


def test_present_starts_committed_definition_by_catalog_id() -> None:
    from plugins.kits.authoring import land
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        published = land(host).commit(_wizard_body("authored-start"))
        catalog_id = published["name"]
        fetched = host.definitions.get_flow(catalog_id)
        assert fetched["name"] == "authored-start"

        kit = bind(host, surface="embedded", origin="test")
        kit.start(catalog_id, by_id=True, job_id="job-authored-start")

        iid = kit.bound.instance_id
        assert iid
        owned = host.session.list_instances(kit.bound.session_id)
        assert iid in owned
        assert GUIDANCE_INSTANCE_ID not in (kit.bound.metadata or {})

        inst = host.runtime().get_instance(iid)
        assert inst.flow_id == catalog_id
        job = host.runtime().orchestration.get_job("job-authored-start")
        assert job.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (job.metadata or {})

        turn = kit.present()
        assert isinstance(turn, JobContext)
        assert turn.pattern == "wizard"
        payload = {k: getattr(turn, k) for k in turn.__dataclass_fields__}
        for key in _ASSIST_ENVELOPE_KEYS:
            assert key not in payload
    finally:
        host.shutdown()
