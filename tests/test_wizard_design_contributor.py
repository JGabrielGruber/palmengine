"""Tests for wizard pattern design proposal contributor."""

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


def _wizard_flow(*, steps: list[dict]) -> dict:
    return FlowDefinition(
        name="wizard-design-test",
        pattern="wizard",
        options={"steps": steps},
    ).to_dict()


def test_wizard_design_contributor_registered_after_host_start(design_host: ApplicationHost) -> None:
    del design_host
    contributor_ids = {row.contributor_id for row in iter_design_contributors()}
    assert "wizard" in contributor_ids


def test_wizard_contributor_rejects_duplicate_step_slugs(design_host: ApplicationHost) -> None:
    body = _wizard_flow(
        steps=[
            {"slug": "note", "title": "Note", "prompt": "Note?"},
            {"slug": "note", "title": "Again", "prompt": "Again?"},
        ],
    )
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("duplicate" in blocker.lower() for blocker in validation["blockers"])


def test_wizard_contributor_rejects_collection_without_item_fields(design_host: ApplicationHost) -> None:
    body = _wizard_flow(
        steps=[
            {
                "slug": "items",
                "title": "Items",
                "prompt": "Items?",
                "step_kind": "collection",
            },
        ],
    )
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("item_fields" in blocker for blocker in validation["blockers"])


def test_wizard_contributor_rejects_duplicate_collection_field_slugs(design_host: ApplicationHost) -> None:
    body = _wizard_flow(
        steps=[
            {
                "slug": "items",
                "title": "Items",
                "prompt": "Items?",
                "step_kind": "collection",
                "item_fields": [
                    {"slug": "title", "title": "Title", "prompt": "Title?"},
                    {"slug": "title", "title": "Dup", "prompt": "Dup?"},
                ],
            },
        ],
    )
    result = design_host.design.propose_flow(body)
    validation = result["validation"]
    assert validation["valid"] is False
    assert any("duplicate" in blocker.lower() for blocker in validation["blockers"])


def test_wizard_contributor_allows_valid_flow(design_host: ApplicationHost) -> None:
    body = _wizard_flow(
        steps=[
            {"slug": "note", "title": "Note", "prompt": "Note?"},
        ],
    )
    result = design_host.design.propose_flow(body)
    assert result["validation"]["valid"] is True
    assert result["validation"]["blockers"] == []