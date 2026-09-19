"""0.70.4 — thin apply speaks a file snapshot; present drives.

Dogfood on embedded: pack waits; leaf commits apply via adapter; resource
lands via host.definitions.create_resource; present starts apply by catalog
id; apply writes snapshot data; waits on confirm; present submit completes.

Not a definition revision. Not Design. Not Assist. Not land verbs on present.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from examples.definitions.authoring_apply import (
    AUTHORING_APPLY_FLOW,
    AUTHORING_SNAPSHOT_DATA,
    AUTHORING_SNAPSHOT_RESOURCE,
    snapshot_resource_body,
)
from examples.definitions.authoring_pack import AUTHORING_PACK_FLOW
from palm.app.host.application_host import ApplicationHost
from palm.common.job_inspection import JobContext
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.core.orchestration import JobStatus
from palm.kits.present import GUIDANCE_INSTANCE_ID
from palm.patterns.wizard.bindings.context.keys import WizardKeys

_ASSIST_ENVELOPE_KEYS = (
    "question",
    "handoff_ready",
    "inspect_catalog",
    "compose",
    "scenario_id",
    "operator_mode",
)

_APPLY_PATH = Path(__file__).resolve().parents[1] / "examples/definitions/authoring_apply.py"


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def test_authoring_apply_is_thin_wizard_not_policy() -> None:
    assert AUTHORING_APPLY_FLOW.name == "authoring-apply"
    assert AUTHORING_APPLY_FLOW.definition_id == "authoring-apply"
    assert AUTHORING_APPLY_FLOW.pattern == "wizard"

    options = AUTHORING_APPLY_FLOW.options or {}
    steps = options.get("steps") or []
    assert len(steps) == 2
    resource, confirm = steps
    assert resource.get("step_kind") == "resource"
    assert resource.get("resource_ref") == "authoring-snapshot"
    assert confirm.get("slug") == "confirm"
    assert confirm.get("field_type") == "text"
    assert "threshold" not in json.dumps(options)
    assert AUTHORING_SNAPSHOT_RESOURCE.provider == "file"
    assert AUTHORING_SNAPSHOT_RESOURCE.action == "write"
    assert AUTHORING_SNAPSHOT_DATA == {"note": "rules-as-data"}
    assert "pattern" not in AUTHORING_SNAPSHOT_DATA


def test_authoring_apply_module_does_not_import_assist() -> None:
    tree = ast.parse(_APPLY_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("palm.services.assist")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("palm.services.assist")
            for alias in node.names:
                assert alias.name != "AssistContributor"


def test_pack_wait_leaf_commit_apply_snapshot_present_drive(tmp_path: Path) -> None:
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
        kit = bind(host, surface="embedded", origin="test")
        assert kit.guidance_definition_id is None
        kit.start("authoring-pack", by_id=True, job_id="job-authoring-pack")
        pack_iid = kit.bound.instance_id
        assert pack_iid
        assert GUIDANCE_INSTANCE_ID not in (kit.bound.metadata or {})
        assert _job(host, "job-authoring-pack").status == JobStatus.WAITING_FOR_INPUT

        kit.submit("thin-apply")
        assert _job(host, "job-authoring-pack").status == JobStatus.WAITING_FOR_INPUT

        published = land(host).commit(AUTHORING_APPLY_FLOW.to_dict())
        apply_id = published["name"]
        assert apply_id == "authoring-apply"
        fetched = host.definitions.get_flow("authoring-apply")
        assert fetched["name"] == "authoring-apply"

        resource_row = host.definitions.create_resource(
            snapshot_resource_body(documents_root=str(documents_root))
        )
        assert resource_row["name"] == "authoring-snapshot"
        catalog_resource = host.definitions.get_resource("authoring-snapshot")
        assert catalog_resource["provider"] == "file"
        assert catalog_resource["action"] == "write"

        kit.start(apply_id, by_id=True, job_id="job-authoring-apply")
        apply_iid = kit.bound.instance_id
        assert apply_iid
        assert apply_iid != pack_iid
        owned = host.session.list_instances(kit.bound.session_id)
        assert pack_iid in owned
        assert apply_iid in owned

        apply_job = _job(host, "job-authoring-apply")
        assert apply_job.status == JobStatus.WAITING_FOR_INPUT
        assert apply_job.state.get(WizardKeys.CURRENT_STEP) == "confirm"
        assert snapshot_path.is_file()
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert payload == AUTHORING_SNAPSHOT_DATA
        assert payload.get("kind") != "flow"
        assert "pattern" not in payload

        turn = kit.present()
        assert isinstance(turn, JobContext)
        assert turn.pattern == "wizard"
        assert turn.step == "confirm"
        payload_fields = {k: getattr(turn, k) for k in turn.__dataclass_fields__}
        for key in _ASSIST_ENVELOPE_KEYS:
            assert key not in payload_fields

        kit.submit("yes")
        done = _job(host, "job-authoring-apply")
        assert done.status == JobStatus.SUCCEEDED
        assert _job(host, "job-authoring-pack").status == JobStatus.WAITING_FOR_INPUT

        with pytest.raises(DefinitionNotFoundServiceError):
            host.definitions.get_flow("authoring-snapshot")
        assert host.definitions.get_flow("authoring-apply")["name"] == "authoring-apply"
    finally:
        host.shutdown()
