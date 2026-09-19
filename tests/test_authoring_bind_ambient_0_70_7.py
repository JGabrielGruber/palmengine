"""0.70.7 — bound() walks the started host, not a land() stash.

land(host) is the library door. Job leaf still walks bound().commit.
Host start already binds the runtime. Definitions come from that host.
Not a second kit-global. Not palm create_flow. Not land verbs on present.
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


def _wizard_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


def test_bound_commits_after_host_start_without_land() -> None:
    from palm.kits.authoring import bound

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        published = bound().commit(_wizard_body("authored-from-bound"))
        assert published["name"] == "authored-from-bound"
        fetched = host.definitions.get_flow("authored-from-bound")
        assert fetched["name"] == "authored-from-bound"
    finally:
        host.shutdown()


def test_pack_job_leaf_still_walks_bound_after_library_land() -> None:
    from palm.kits.authoring import land
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        land(host).commit(AUTHORING_PACK_FLOW.to_dict())
        land(host).commit(AUTHORING_COMMIT_RESOURCE.to_dict())

        kit = bind(host, surface="embedded", origin="test")
        kit.start("authoring-pack", by_id=True, job_id="job-authoring-pack-bound")
        assert _job(host, "job-authoring-pack-bound").status == JobStatus.WAITING_FOR_INPUT

        kit.submit(_wizard_body("authored-after-bind"))
        assert _job(host, "job-authoring-pack-bound").status == JobStatus.SUCCEEDED
        assert host.definitions.get_flow("authored-after-bind")["name"] == "authored-after-bind"
    finally:
        host.shutdown()
