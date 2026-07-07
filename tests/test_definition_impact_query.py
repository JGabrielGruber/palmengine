"""Tests for definition revision impact analysis (0.24.2)."""

from __future__ import annotations

from palm.common.persistence.definition_impact import analyze_definition_impact
from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    migration_registry,
    register_migration_rule,
)


def setup_function() -> None:
    migration_registry.clear()
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.definitions import FlowDefinition
from palm.instances import ProcessInstance


def _repo_with_revisions() -> DefinitionRepository:
    repo = DefinitionRepository()
    repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 1}),
    )
    repo.publish_flow_revision(
        FlowDefinition(name="onboard", pattern="wizard", options={"step_count": 2}),
    )
    return repo


def test_analyze_impact_lists_instances_behind_latest() -> None:
    repo = _repo_with_revisions()
    instances = [
        ProcessInstance(
            instance_id="inst-1",
            job_id="job-1",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {}},
            flow_definition=repo.get_flow_by_id("onboard", revision=1).to_dict(),
            pattern="wizard",
            flow_id="onboard",
            flow_revision=1,
        ),
        ProcessInstance(
            instance_id="inst-2",
            job_id="job-2",
            status="SUCCEEDED",
            state_snapshot={},
            flow_definition=repo.get_flow_by_id("onboard", revision=2).to_dict(),
            pattern="wizard",
            flow_id="onboard",
            flow_revision=2,
        ),
    ]
    report = analyze_definition_impact(repo, instances, flow_id="onboard")
    assert report["latest_revision"] == 2
    assert report["target_revision"] == 2
    assert report["summary"]["total"] == 2
    assert report["summary"]["behind_latest"] == 1
    assert len(report["instances"]) == 1
    assert report["instances"][0]["instance_id"] == "inst-1"
    assert report["instances"][0]["current_revision"] == 1
    assert report["instances"][0]["compatibility"] == "snapshot_only"


def test_analyze_impact_marks_compatible_when_rule_exists() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="onboard",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (True, []),
            _migrate_state=lambda ctx: ctx.state,
        ),
    )
    repo = _repo_with_revisions()
    instances = [
        ProcessInstance(
            instance_id="inst-1",
            job_id="job-1",
            status="WAITING_FOR_INPUT",
            state_snapshot={"answers": {"name": "Ada"}},
            flow_definition=repo.get_flow_by_id("onboard", revision=1).to_dict(),
            pattern="wizard",
            flow_id="onboard",
            flow_revision=1,
        ),
    ]
    report = analyze_definition_impact(repo, instances, flow_id="onboard")
    row = report["instances"][0]
    assert row["compatible"] is True
    assert row["compatibility"] == "compatible"
    assert report["summary"]["compatible"] == 1


def test_analyze_impact_marks_blocked_when_rule_rejects() -> None:
    register_migration_rule(
        CallableMigrationRule(
            flow_id="onboard",
            from_revision=1,
            to_revision=2,
            _can_migrate=lambda _ctx: (False, ["unsupported answers"]),
            _migrate_state=lambda ctx: ctx.state,
        ),
    )
    repo = _repo_with_revisions()
    instances = [
        ProcessInstance(
            instance_id="inst-1",
            job_id="job-1",
            status="WAITING_FOR_INPUT",
            state_snapshot={},
            flow_definition=repo.get_flow_by_id("onboard", revision=1).to_dict(),
            pattern="wizard",
            flow_id="onboard",
            flow_revision=1,
        ),
    ]
    report = analyze_definition_impact(repo, instances, flow_id="onboard")
    row = report["instances"][0]
    assert row["compatible"] is False
    assert row["compatibility"] == "blocked"
    assert row["blockers"] == ["unsupported answers"]
    assert report["summary"]["blocked"] == 1


def test_legacy_instance_infers_revision_from_snapshot() -> None:
    repo = _repo_with_revisions()
    instances = [
        ProcessInstance(
            instance_id="inst-legacy",
            job_id="job-1",
            status="WAITING_FOR_INPUT",
            state_snapshot={},
            flow_definition={"name": "onboard", "pattern": "wizard", "revision": 1, "options": {}},
            pattern="wizard",
            flow_id="onboard",
            flow_revision=None,
        ),
    ]
    report = analyze_definition_impact(repo, instances, flow_id="onboard")
    assert report["instances"][0]["current_revision"] == 1