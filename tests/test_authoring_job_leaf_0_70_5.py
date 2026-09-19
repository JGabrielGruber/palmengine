"""0.70.5 — a leaf of the pack run commits via the authoring adapter.

Present starts the pack. Submit is a FlowDefinition body. A resource step
in that job walks land/commit. Pytest is not the leaf. Present starts the
new catalog id.

Not palm create_flow. Not land verbs on present. Not Design. Not Assist.
"""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
from examples.definitions.authoring_pack import (
    AUTHORING_COMMIT_RESOURCE,
    AUTHORING_PACK_FLOW,
)


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def _shape_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


def test_pack_job_leaf_commits_submitted_shape_via_adapter() -> None:
    from palm.kits.authoring import land
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        land(host).commit(AUTHORING_PACK_FLOW.to_dict())
        land(host).commit(AUTHORING_COMMIT_RESOURCE.to_dict())

        kit = bind(host, surface="embedded", origin="test")
        kit.start("authoring-pack", by_id=True, job_id="job-authoring-pack")
        assert _job(host, "job-authoring-pack").status == JobStatus.WAITING_FOR_INPUT

        shape = _shape_body("authored-from-pack")
        names_before = {row["name"] for row in host.definitions.list_flows()}
        assert "authored-from-pack" not in names_before

        kit.submit(shape)

        assert _job(host, "job-authoring-pack").status == JobStatus.SUCCEEDED
        fetched = host.definitions.get_flow("authored-from-pack")
        assert fetched["name"] == "authored-from-pack"

        kit.start("authored-from-pack", by_id=True, job_id="job-authored-from-pack")
        assert _job(host, "job-authored-from-pack").status == JobStatus.WAITING_FOR_INPUT
        inst = host.runtime().get_instance(kit.bound.instance_id)
        assert inst.flow_id == "authored-from-pack"
    finally:
        host.shutdown()
