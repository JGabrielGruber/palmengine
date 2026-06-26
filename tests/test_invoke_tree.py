"""Tests for compositional invoke tree builder."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.providers.palm.provider import PalmProvider
from palm.runtimes.embedded import EmbeddedRuntime


def _child_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-child-wizard",
        name="child-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "question", "title": "Question", "prompt": "Child question?"},
            ],
        },
    )


def _parent_wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-parent-wizard",
        name="parent-wizard",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn_child",
                    "title": "Spawn Child Wizard",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-wizard",
                    "output_key": "child_job",
                },
            ],
        },
    )


def _submit_child_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-submit-child-wizard",
        name="submit-child-wizard",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-wizard",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    rt.repository.save_flow(_child_wizard_flow())
    rt.repository.save_flow(_parent_wizard_flow())
    rt.repository.save_resource(_submit_child_resource())
    yield rt
    rt.stop()
    clear_palm_runtime()


def _palm_provider() -> PalmProvider:
    provider = PalmProvider(name="palm")
    provider.connect()
    return provider


def test_build_invoke_tree_reports_active_child(runtime: EmbeddedRuntime) -> None:
    _palm_provider()
    parent_job = runtime.submit_flow("parent-wizard")
    runtime.wait_until_idle(timeout=5)
    assert parent_job.status == JobStatus.WAITING_FOR_INPUT

    parent_instance_id = str(parent_job.metadata["instance_id"])
    tree = build_invoke_tree(runtime, parent_instance_id, base_url="http://localhost:8002")

    assert tree["instance_id"] == parent_instance_id
    assert tree["root"]["flow"] == "parent-wizard"
    assert tree["active_child"] is not None
    assert tree["active_child"]["status"] == JobStatus.WAITING_FOR_INPUT.value
    assert tree["links"]["explorer"] == f"http://localhost:8002/explorer/instances/{parent_instance_id}"