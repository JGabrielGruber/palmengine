"""Integration tests for design_proposal_demo example (0.25.6)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, DeploymentProfile
from palm.app.settings import PalmSettings
from palm.common.patterns._registry import get_design_contributor_hook
from palm.services.design.contributors import reset_design_contributor_wiring
from palm.services.design.registry import clear_design_contributors


@pytest.fixture
def demo_host() -> Iterator[ApplicationHost]:
    clear_design_contributors()
    reset_design_contributor_wiring()
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    yield host
    host.shutdown()


def test_design_proposal_demo_pipeline_commits_and_migrates(demo_host: ApplicationHost) -> None:
    from examples.definitions.design_proposal_demo import (
        _seed_revision_one_instance,
        run_design_proposal_pipeline,
    )

    instance_id = "inst-design-demo-test"
    _seed_revision_one_instance(demo_host, instance_id=instance_id)

    preview = run_design_proposal_pipeline(
        demo_host,
        instance_id=instance_id,
        preview_only=True,
    )
    assert preview["phase"] == "preview"
    assert preview["validation"]["valid"] is True
    assert preview["impact"]["summary"]["compatible"] == 1

    result = run_design_proposal_pipeline(
        demo_host,
        instance_id=instance_id,
        preview_only=False,
    )
    assert result["committed"]["revision"] == 2
    assert result["committed"]["migrations"]["succeeded"] == 1
    assert result["instance"]["flow_revision"] == 2
    assert result["instance"]["migrated"] is True


def test_design_proposal_demo_register_definitions_publishes_meta_flow() -> None:
    from examples.definitions import design_proposal_demo
    from palm.common.persistence.definition_repository import DefinitionRepository

    repository = DefinitionRepository()
    design_proposal_demo.register_definitions(repository)

    flow = repository.get_flow("design-proposal-demo")
    assert flow.name == "design-proposal-demo"
    assert flow.options.get("commit_hook") == "apply_design_proposal"

    source = repository.get_flow("design-demo-flow", revision=1)
    assert source.revision == 1


def test_design_proposal_demo_commit_handler_preview(demo_host: ApplicationHost) -> None:
    from examples.definitions.design_proposal_demo import (
        _make_apply_design_proposal_handler,
        _seed_revision_one_instance,
    )
    from palm.patterns.wizard.bindings.compensation.handler import CommitContext

    instance_id = "inst-design-demo-preview"
    _seed_revision_one_instance(demo_host, instance_id=instance_id)

    from examples.definitions.design_proposal_demo import attach_design_host

    revisions_before = len(demo_host.definitions.list_flow_revisions("design-demo-flow"))
    attach_design_host(demo_host)
    handler = _make_apply_design_proposal_handler(demo_host.definitions._repository)
    ctx = CommitContext(
        wizard_name="design-proposal-demo",
        state=object(),  # type: ignore[arg-type]
        answers={
            "instance_id": instance_id,
            "confirm": "yes",
            "action": "preview",
        },
        hook_name="apply_design_proposal",
    )
    result = handler(ctx)
    assert result.ok is True
    assert result.data["phase"] == "preview"
    assert result.data["validation"]["valid"] is True
    assert result.data["impact"]["summary"]["compatible"] == 1

    # Preview must not publish a new revision on the shared storage host.
    assert len(demo_host.definitions.list_flow_revisions("design-demo-flow")) == revisions_before


def test_wizard_and_pipeline_design_hooks_registered() -> None:
    from palm.patterns.pipeline.app import pipeline_app
    from palm.patterns.wizard.app import wizard_app

    wizard_app.register()
    pipeline_app.register()
    assert get_design_contributor_hook("wizard") is not None
    assert get_design_contributor_hook("pipeline") is not None