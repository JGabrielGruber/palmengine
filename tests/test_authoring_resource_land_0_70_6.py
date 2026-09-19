"""0.70.6 — adapter commit lands a ResourceDefinition; pack leaf is the door.

Library land/commit of a resource is the same adapter. A pack run submits a
ResourceDefinition mapping; authoring-commit walks bound().commit. Pytest is
not that leaf. Present then starts the apply that speaks the snapshot data.

Not palm create_flow. Not create_resource bypass. Not a fifth wizard.
Not land verbs on present. Not Design. Not Assist.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.definitions.authoring_apply import (
    AUTHORING_APPLY_FLOW,
    AUTHORING_SNAPSHOT_DATA,
    snapshot_resource_body,
)
from examples.definitions.authoring_pack import (
    AUTHORING_COMMIT_RESOURCE,
    AUTHORING_PACK_FLOW,
)
from palm.app.host.application_host import ApplicationHost
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.core.orchestration import JobStatus
from palm.definitions import ResourceDefinition
from palm.patterns.wizard.bindings.context.keys import WizardKeys


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def test_land_commits_resource_on_embedded_definitions() -> None:
    from palm.kits.authoring import land

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        body = ResourceDefinition(
            id="authored-resource",
            name="authored-resource",
            provider="file",
            action="write",
            resource_id="authored/note.json",
            params={"format": "json", "content": {"note": "catalog"}},
        ).to_dict()
        published = land(host).commit(body)
        assert published["name"] == "authored-resource"
        assert published["kind"] == "resource"
        fetched = host.definitions.get_resource("authored-resource")
        assert fetched["provider"] == "file"
        with pytest.raises(DefinitionNotFoundServiceError):
            host.definitions.get_flow("authored-resource")
    finally:
        host.shutdown()


def test_commit_unknown_kind_fails() -> None:
    from palm.kits.authoring import land

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        with pytest.raises(ValueError, match="kind"):
            land(host).commit({"kind": "dashboard", "name": "nope"})
    finally:
        host.shutdown()


def test_pack_job_leaf_lands_snapshot_then_present_drives_apply(
    tmp_path: Path,
) -> None:
    from palm.kits.authoring import land
    from palm.kits.present import bind

    documents_root = tmp_path / "documents"
    snapshot_path = documents_root / "authoring" / "snapshot.json"

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        land(host).commit(AUTHORING_PACK_FLOW.to_dict())
        land(host).commit(AUTHORING_COMMIT_RESOURCE.to_dict())

        kit = bind(host, surface="embedded", origin="test")
        kit.start("authoring-pack", by_id=True, job_id="job-authoring-snapshot")
        assert _job(host, "job-authoring-snapshot").status == JobStatus.WAITING_FOR_INPUT

        snapshot = snapshot_resource_body(documents_root=str(documents_root))
        names_before = {row["name"] for row in host.definitions.list_resources()}
        assert "authoring-snapshot" not in names_before

        kit.submit(snapshot)

        assert _job(host, "job-authoring-snapshot").status == JobStatus.SUCCEEDED
        catalog_resource = host.definitions.get_resource("authoring-snapshot")
        assert catalog_resource["provider"] == "file"
        assert catalog_resource["action"] == "write"
        with pytest.raises(DefinitionNotFoundServiceError):
            host.definitions.get_flow("authoring-snapshot")

        kit.start("authoring-pack", by_id=True, job_id="job-authoring-apply-shape")
        kit.submit(AUTHORING_APPLY_FLOW.to_dict())
        assert _job(host, "job-authoring-apply-shape").status == JobStatus.SUCCEEDED
        assert host.definitions.get_flow("authoring-apply")["name"] == "authoring-apply"

        kit.start("authoring-apply", by_id=True, job_id="job-authoring-apply")
        apply_job = _job(host, "job-authoring-apply")
        assert apply_job.status == JobStatus.WAITING_FOR_INPUT
        assert apply_job.state.get(WizardKeys.CURRENT_STEP) == "confirm"
        assert snapshot_path.is_file()
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert payload == AUTHORING_SNAPSHOT_DATA
        assert payload.get("kind") != "flow"

        kit.submit("yes")
        assert _job(host, "job-authoring-apply").status == JobStatus.SUCCEEDED
    finally:
        host.shutdown()
