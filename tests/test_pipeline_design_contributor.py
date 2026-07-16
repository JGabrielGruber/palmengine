"""Tests for pipeline pattern design proposal contributor (0.25.5)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.settings import PalmSettings
from palm.definitions import FlowDefinition
from palm.services.design.registry import clear_design_contributors, iter_design_contributors


@pytest.fixture
def design_settings() -> PalmSettings:
    return PalmSettings.for_tests(load_examples=False)


@pytest.fixture
def design_host(design_settings: PalmSettings) -> Iterator[ApplicationHost]:
    host = ApplicationHost(settings=design_settings, profile=DeploymentProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def setup_function() -> None:
    from palm.services.design.contributors import reset_design_contributor_wiring

    clear_design_contributors()
    reset_design_contributor_wiring()


def _pipeline_flow(*, steps: list[dict]) -> dict:
    return FlowDefinition(
        name="pipeline-design-test",
        pattern="pipeline",
        options={"steps": steps},
    ).to_dict()


def test_pipeline_design_contributor_registered_after_host_start(design_host: ApplicationHost) -> None:
    del design_host
    contributor_ids = {row.contributor_id for row in iter_design_contributors()}
    assert "pipeline" in contributor_ids


def test_pipeline_contributor_rejects_empty_steps(design_host: ApplicationHost) -> None:
    body = _pipeline_flow(steps=[])
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("steps" in blocker.lower() for blocker in validation["blockers"])


def test_pipeline_contributor_rejects_step_without_rule_or_chain(design_host: ApplicationHost) -> None:
    body = _pipeline_flow(
        steps=[
            {
                "name": "broken",
                "source_key": "payload",
            },
        ],
    )
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("rule or chain" in blocker for blocker in validation["blockers"])


def test_pipeline_contributor_rejects_duplicate_step_names(design_host: ApplicationHost) -> None:
    body = _pipeline_flow(
        steps=[
            {
                "name": "rename",
                "source_key": "payload",
                "target_key": "user",
                "rule": "rename_field",
                "options": {"from_key": "first_name", "to_key": "name"},
            },
            {
                "name": "rename",
                "source_key": "user",
                "target_key": "out",
                "rule": "rename_field",
                "options": {"from_key": "name", "to_key": "full_name"},
            },
        ],
    )
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("duplicate" in blocker.lower() for blocker in validation["blockers"])


def test_pipeline_contributor_allows_valid_flow(design_host: ApplicationHost) -> None:
    body = _pipeline_flow(
        steps=[
            {
                "name": "rename",
                "source_key": "payload",
                "target_key": "user",
                "rule": "rename_field",
                "options": {"from_key": "first_name", "to_key": "name"},
            },
        ],
    )
    result = design_host.design.propose_flow(body)
    assert result["validation"]["valid"] is True
    assert result["validation"]["blockers"] == []