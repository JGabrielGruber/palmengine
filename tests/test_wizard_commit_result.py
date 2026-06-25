"""Wizard commit result propagation to job.result and compositional parents."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.patterns.wizard import WizardKeys
from palm.patterns.wizard.bindings.compensation.handler import CommitResult, default_commit_registry
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState
from palm.core.behavior_tree import PatternStatus
from palm.patterns.wizard import WizardConfig, WizardPattern, WizardStepConfig


FLOW_CAPTURE_NODE = "capture-node"
FLOW_CAPTURE_KNOWLEDGE = "capture-knowledge"
COMMIT_HOOK = "test_capture_node_commit"


def _register_capture_commit_hook() -> None:
    default_commit_registry().register(
        COMMIT_HOOK,
        lambda ctx: CommitResult.success(
            {
                "main_node": {
                    "id": "node-test-1",
                    "title": ctx.answers.get("title"),
                }
            }
        ),
    )


def _child_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-capture-node",
        name=FLOW_CAPTURE_NODE,
        pattern="wizard",
        options={
            "include_summary": False,
            "include_commit": True,
            "commit_hook": COMMIT_HOOK,
            "steps": [
                {
                    "slug": "title",
                    "title": "Title",
                    "prompt": "Node title?",
                    "validation": [{"rule": "min_length", "params": {"min": 3}}],
                },
            ],
        },
    )


def _parent_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-capture-knowledge",
        name=FLOW_CAPTURE_KNOWLEDGE,
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "goal",
                    "title": "Goal",
                    "prompt": "What are you capturing?",
                    "validation": [{"rule": "min_length", "params": {"min": 3}}],
                },
                {
                    "slug": "capture_main",
                    "title": "Capture main node",
                    "step_kind": "resource",
                    "resource_ref": "submit-capture-node",
                    "output_key": "capture_main",
                },
                {
                    "slug": "merge_main",
                    "title": "Record main node",
                    "step_kind": "transform",
                    "prompt": "Storing main node reference...",
                    "source_key": "capture_main",
                    "target_key": "main_node",
                    "rule": "jsonpath_extract",
                    "options": {"path": "result.main_node"},
                },
                {
                    "slug": "confirm_done",
                    "title": "Done",
                    "prompt": "Continue?",
                    "field_type": "confirm",
                },
            ],
        },
    )


def _submit_child_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-submit-capture-node",
        name="submit-capture-node",
        provider="palm",
        action="submit_flow",
        resource_id="flow:capture-node",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 10,
        },
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    _register_capture_commit_hook()
    rt = EmbeddedRuntime()
    rt.start()
    rt.repository.save_flow(_child_flow())
    rt.repository.save_flow(_parent_flow())
    rt.repository.save_resource(_submit_child_resource())
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_commit_sets_result_on_state() -> None:
    registry = default_commit_registry()
    registry.register(
        "save_with_payload",
        lambda ctx: CommitResult.success({"stored": True, "name": ctx.answers.get("name")}),
    )
    config = WizardConfig(
        steps=(WizardStepConfig(slug="name", title="Name", prompt="Name?"),),
        include_summary=False,
        include_commit=True,
        commit_hook="save_with_payload",
    )
    state = BlackboardState()
    wizard = WizardPattern(name="w", config=config, commit_registry=registry)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert state.get("__result__") == {"stored": True, "name": "Ada"}
    assert state.get(WizardKeys.COMMIT_RESULT) == {"stored": True, "name": "Ada"}


def test_stored_flow_sets_job_result(runtime: EmbeddedRuntime) -> None:
    job = runtime.submit_flow(FLOW_CAPTURE_NODE)
    runtime.wait_until_idle(timeout=5)

    runtime.provide_input(job.id, "Test Node")
    runtime.wait_until_idle(timeout=5)
    runtime.provide_input(job.id, "yes")
    runtime.wait_until_idle(timeout=5)

    job = runtime.get_job(job.id)
    assert job.status == JobStatus.SUCCEEDED
    assert job.result == {"main_node": {"id": "node-test-1", "title": "Test Node"}}


def test_parent_merge_main_extracts_child_commit_result(runtime: EmbeddedRuntime) -> None:
    parent = runtime.submit_flow(FLOW_CAPTURE_KNOWLEDGE)
    runtime.wait_until_idle(timeout=5)

    runtime.provide_input(parent.id, "Testing knowledge capture")
    runtime.wait_until_idle(timeout=5)

    parent = runtime.get_job(parent.id)
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "capture_main"

    waiting = parent.state.get(WizardKeys.WAITING_FOR_CHILD)
    assert isinstance(waiting, dict)
    child_job_id = str(waiting["child_job_id"])

    runtime.provide_input(child_job_id, "Main Topic")
    runtime.wait_until_idle(timeout=5)
    runtime.provide_input(child_job_id, "yes")
    runtime.wait_until_idle(timeout=10)

    child = runtime.get_job(child_job_id)
    assert child.status == JobStatus.SUCCEEDED
    assert child.result == {"main_node": {"id": "node-test-1", "title": "Main Topic"}}

    parent = runtime.get_job(parent.id)
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "confirm_done"

    answers = parent.state.get(WizardKeys.ANSWERS) or {}
    capture_main = answers.get("capture_main")
    assert isinstance(capture_main, dict)
    assert capture_main.get("status") == JobStatus.SUCCEEDED.value
    assert capture_main.get("result") == {
        "main_node": {"id": "node-test-1", "title": "Main Topic"},
    }
    assert answers.get("main_node") == {"id": "node-test-1", "title": "Main Topic"}