"""0.70.3 — authoring pack wizard present can start and wait.

Purpose lives in a definition. Proof path is adapter land/commit then
present start by catalog id. Pack id stays unnamed; as-built
``authoring-pack``. Job-leaf commit is ``0.70.5``.

Not another generic wizard body. Not design_entry. Not Assist.
"""

from __future__ import annotations

import ast
from pathlib import Path

from examples.definitions.authoring_pack import AUTHORING_PACK_FLOW
from bundles.standard.app.host.application_host import ApplicationHost
from palm.common.job_inspection import JobContext
from palm.core.orchestration import JobStatus
from plugins.kits.present import GUIDANCE_INSTANCE_ID

_ASSIST_ENVELOPE_KEYS = (
    "question",
    "handoff_ready",
    "inspect_catalog",
    "compose",
    "scenario_id",
    "operator_mode",
)

_PACK_PATH = Path(__file__).resolve().parents[1] / "examples/definitions/authoring_pack.py"
_DESIGN_ENTRY_PATH = Path(__file__).resolve().parents[1] / "examples/definitions/design_entry.py"


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def test_authoring_pack_is_purpose_wizard_not_author() -> None:
    assert AUTHORING_PACK_FLOW.name == "authoring-pack"
    assert AUTHORING_PACK_FLOW.definition_id == "authoring-pack"
    assert AUTHORING_PACK_FLOW.pattern == "wizard"
    assert AUTHORING_PACK_FLOW.name != "author"

    options = AUTHORING_PACK_FLOW.options or {}
    assert "handoff_map" not in options
    assert "handoff_flows" not in (options.get("metadata") or {})
    assist = (options.get("metadata") or {}).get("assist") or {}
    assert "handoff_map" not in assist
    assert "handoff_flows" not in assist

    steps = options.get("steps") or []
    assert len(steps) == 2
    assert steps[0].get("slug") == "shape"
    assert steps[1].get("step_kind") == "resource"
    assert steps[1].get("resource_ref") == "authoring-commit"


def test_authoring_pack_module_does_not_import_assist() -> None:
    tree = ast.parse(_PACK_PATH.read_text(encoding="utf-8"))
    forbidden_prefixes = (
        "palm.services.assist",
        "plugins.kits.assist",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_prefixes
                assert not alias.name.startswith("palm.services.assist")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("palm.services.assist")
            for alias in node.names:
                assert alias.name != "AssistContributor"


def test_design_entry_leftover_unchanged() -> None:
    text = _DESIGN_ENTRY_PATH.read_text(encoding="utf-8")
    assert "AssistContributor" in text
    assert "register_assist_contributor" in text
    pack = _PACK_PATH.read_text(encoding="utf-8")
    assert "AssistContributor" not in pack
    assert "register_assist_contributor" not in pack


def test_land_commit_then_present_starts_authoring_pack_and_waits() -> None:
    from plugins.kits.authoring import land
    from plugins.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None

        published = land(host).commit(AUTHORING_PACK_FLOW.to_dict())
        catalog_id = published["name"]
        assert catalog_id == "authoring-pack"
        fetched = host.definitions.get_flow("authoring-pack")
        assert fetched["name"] == "authoring-pack"

        kit = bind(host, surface="embedded", origin="test")
        assert kit.guidance_definition_id is None
        kit.start(catalog_id, by_id=True, job_id="job-authoring-pack")

        iid = kit.bound.instance_id
        assert iid
        owned = host.session.list_instances(kit.bound.session_id)
        assert iid in owned
        assert GUIDANCE_INSTANCE_ID not in (kit.bound.metadata or {})

        inst = host.runtime().get_instance(iid)
        assert inst.flow_id == catalog_id
        job = _job(host, "job-authoring-pack")
        assert job.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (job.metadata or {})

        turn = kit.present()
        assert isinstance(turn, JobContext)
        assert turn.pattern == "wizard"
        payload = {k: getattr(turn, k) for k in turn.__dataclass_fields__}
        for key in _ASSIST_ENVELOPE_KEYS:
            assert key not in payload

        names_before = {row["name"] for row in host.definitions.list_flows()}
        jobs_before = {j.id for j in host.runtime().orchestration.list_jobs()}
        assert "authoring-pack" in names_before
        assert "job-authoring-pack" in jobs_before
    finally:
        host.shutdown()
