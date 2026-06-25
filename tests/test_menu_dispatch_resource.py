"""Menu-style wizard dispatch resource steps (KnowKey-like compositional routing)."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.patterns.wizard import WizardKeys
from palm.common.interactive_runtime import provide_interactive_input_for_instance
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.runtimes.cli.shared.job_inspect import inspect_job_json
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.server.surfaces.ssr.explorer.forms import wizard_input_form


FLOW_CHILD = "capture-knowledge"
FLOW_MENU = "main-menu"

MENU_ROUTE_TABLE = {
    "capture_knowledge": FLOW_CHILD,
}


def _child_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-capture-knowledge",
        name=FLOW_CHILD,
        pattern="wizard",
        options={
            "steps": [
                {"slug": "goal", "title": "Goal", "prompt": "What are you capturing?"},
            ],
        },
    )


def _menu_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-main-menu",
        name=FLOW_MENU,
        pattern="wizard",
        options={
            "introduction_slug": "welcome",
            "steps": [
                {
                    "slug": "welcome",
                    "title": "Welcome",
                    "step_kind": "introduction",
                    "prompt": "Welcome to compose.",
                    "field_type": "confirm",
                },
                {
                    "slug": "menu_action",
                    "title": "Menu",
                    "field_type": "choice",
                    "choices": ["capture_knowledge"],
                    "prompt": "Choose an action",
                },
                {
                    "slug": "route_menu",
                    "title": "Route",
                    "step_kind": "transform",
                    "source_key": "menu_action",
                    "target_key": "route_target",
                    "rule": "lookup",
                    "options": {"table": MENU_ROUTE_TABLE},
                },
                {
                    "slug": "dispatch",
                    "title": "Launching flow",
                    "step_kind": "resource",
                    "resource_ref": "route-flow",
                    "action": "submit_flow",
                    "params": {
                        "target": "{{ state.route_target }}",
                        "wait": True,
                        "wait_mode": "until_input",
                        "timeout_seconds": 5,
                    },
                    "output_key": "dispatch_result",
                },
            ],
        },
    )


def _route_resource() -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-route-flow",
        name="route-flow",
        provider="palm",
        action="submit_flow",
        params={
            "target": "{{ state.route_target }}",
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    rt.repository.save_flow(_child_flow())
    rt.repository.save_flow(_menu_flow())
    rt.repository.save_resource(_route_resource())
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_menu_dispatch_spawns_child_after_menu_choice(runtime: EmbeddedRuntime) -> None:
    parent = runtime.submit_flow(FLOW_MENU)
    runtime.wait_until_idle(timeout=5)

    assert parent.status == JobStatus.WAITING_FOR_INPUT
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "welcome"

    runtime.provide_input(parent.id, True)
    runtime.wait_until_idle(timeout=5)

    parent = runtime.get_job(parent.id)
    assert parent.status == JobStatus.WAITING_FOR_INPUT
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "menu_action"

    runtime.provide_input(parent.id, "capture_knowledge")
    runtime.wait_until_idle(timeout=5)

    parent = runtime.get_job(parent.id)
    assert parent.status == JobStatus.WAITING_FOR_INPUT
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "dispatch"

    answers = parent.state.get(WizardKeys.ANSWERS) or {}
    assert answers.get("route_target") == FLOW_CHILD

    context = inspect_job_json(parent)
    assert context.get("waiting_for_child") is True
    assert context.get("waiting_for_child_job_id")
    assert "Waiting for nested wizard" in (context.get("prompt") or "")

    waiting = parent.state.get(WizardKeys.WAITING_FOR_CHILD)
    assert isinstance(waiting, dict)
    child_job_id = waiting["child_job_id"]
    assert child_job_id

    child = runtime.get_job(str(child_job_id))
    assert child.status == JobStatus.WAITING_FOR_INPUT
    assert child.metadata.get("__palm:parent_job_id") == parent.id


def test_menu_dispatch_via_instance_input(runtime: EmbeddedRuntime) -> None:
    parent = runtime.submit_flow(FLOW_MENU)
    runtime.wait_until_idle(timeout=5)

    instance_id = str(parent.metadata.get("instance_id") or parent.id)

    runtime.provide_input(parent.id, True)
    runtime.wait_until_idle(timeout=5)
    runtime.provide_input(parent.id, "capture_knowledge")
    runtime.wait_until_idle(timeout=5)

    parent = runtime.get_job(parent.id)
    assert parent.state.get(WizardKeys.CURRENT_STEP) == "dispatch"

    provide_interactive_input_for_instance(runtime, instance_id, "ignored")
    runtime.wait_until_idle(timeout=5)

    parent = runtime.get_job(parent.id)
    context = inspect_job_json(parent)
    assert context.get("step") == "dispatch"
    assert context.get("waiting_for_child") is True


def test_menu_dispatch_spawns_child_with_queued_scheduler() -> None:
    rt = EmbeddedRuntime()
    rt.start(scheduler="queued")
    try:
        rt.repository.save_flow(_child_flow())
        rt.repository.save_flow(_menu_flow())
        rt.repository.save_resource(_route_resource())

        parent = rt.submit_flow(FLOW_MENU)
        rt.wait_until_idle(timeout=5)

        rt.provide_input(parent.id, True)
        rt.wait_until_idle(timeout=5)
        rt.provide_input(parent.id, "capture_knowledge")
        rt.wait_until_idle(timeout=10)

        parent = rt.get_job(parent.id)
        assert parent.status == JobStatus.WAITING_FOR_INPUT
        assert parent.state.get(WizardKeys.CURRENT_STEP) == "dispatch"

        context = inspect_job_json(parent)
        assert context.get("waiting_for_child") is True

        waiting = parent.state.get(WizardKeys.WAITING_FOR_CHILD)
        assert isinstance(waiting, dict)
        child = rt.get_job(str(waiting["child_job_id"]))
        assert child.status == JobStatus.WAITING_FOR_INPUT
    finally:
        rt.stop()
        clear_palm_runtime()


def test_wizard_resource_form_has_no_text_input() -> None:
    html = wizard_input_form(
        "inst-1",
        {
            "slug": "dispatch",
            "title": "Launching flow",
            "prompt": "Invoking resource 'route-flow' → dispatch_result",
            "field_type": "resource",
            "step_kind": "resource",
            "auto_advance": True,
        },
    )
    assert 'name="value"' not in html
    assert "resource-step-panel" in html
    assert "resume-wizard-tick" in html