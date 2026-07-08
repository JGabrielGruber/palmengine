"""Tests for wizard ``step_kind: branch`` — state-driven BT routing."""

from __future__ import annotations

from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.behavior_tree import PatternStatus
from palm.core.resource import ResourceEngine
from palm.definitions import FlowDefinition
from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
from palm.patterns.wizard.flow.phases._base import provide_wizard_input
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


def _branch_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-branch-test",
        name="branch-test",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "flag",
                    "step_kind": "transform",
                    "source_key": "seed",
                    "target_key": "is_returning",
                    "rule": "conditional",
                    "options": {"field": "returning", "is_truthy": True, "then": True, "else": False},
                },
                {
                    "slug": "gate",
                    "step_kind": "branch",
                    "title": "Gate",
                    "when": {"field": "is_returning", "is_truthy": True},
                    "then": [
                        {
                            "slug": "then_topic",
                            "step_kind": "transform",
                            "source_key": "seed",
                            "target_key": "topic_prompt",
                            "rule": "string_format",
                            "options": {"template": "welcome back"},
                        },
                    ],
                    "else": [
                        {
                            "slug": "reputation",
                            "title": "Reputation",
                            "prompt": "Pick reputation",
                            "field_type": "choice",
                            "choices": ["friend", "stranger"],
                        },
                    ],
                },
                {
                    "slug": "topic",
                    "title": "Hub",
                    "prompt": "{{ state.topic_prompt }}",
                    "field_type": "text",
                    "required": False,
                },
            ],
        },
    )


def _tree():
    flow = _branch_flow()
    runtime = EmbeddedRuntime()
    runtime.start()
    bind_palm_runtime(runtime)
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(DefinitionRepository()))
    options = parse_wizard_flow_options(flow.options)
    config = wizard_config_from_options(options)
    root, _sequence = build_wizard_tree("branch-test", config, resource_engine=engine)
    return root, runtime, engine


def test_branch_config_flattens_nested_slugs() -> None:
    flow = _branch_flow()
    config = wizard_config_from_options(parse_wizard_flow_options(flow.options))
    slugs = [step.slug for step in config.iter_all_steps()]
    assert "gate" in slugs
    assert "reputation" in slugs
    assert "then_topic" in slugs


def test_branch_else_arm_runs_for_first_time_traveler() -> None:
    root, runtime, engine = _tree()
    state = BlackboardState({"seed": {"returning": False}})
    try:
        while state.get(WizardKeys.CURRENT_STEP) != "reputation":
            status = root.tick(state)
            if status == PatternStatus.WAITING_FOR_INPUT:
                slug = state.get(WizardKeys.CURRENT_STEP)
                if slug == "reputation":
                    break
                provide_wizard_input(state, "placeholder")
        assert state.get(WizardKeys.CURRENT_STEP) == "reputation"
    finally:
        engine.shutdown()
        runtime.stop()
        clear_palm_runtime()


def test_branch_then_arm_skips_reputation_for_returning_traveler() -> None:
    root, runtime, engine = _tree()
    state = BlackboardState({"seed": {"returning": True}})
    try:
        for _ in range(30):
            slug = state.get(WizardKeys.CURRENT_STEP)
            if slug == "topic":
                break
            if slug == "reputation":
                raise AssertionError("returning traveler should not see reputation step")
            status = root.tick(state)
            if status == PatternStatus.WAITING_FOR_INPUT:
                provide_wizard_input(state, "ok")
        answers = state.get(WizardKeys.ANSWERS) or {}
        assert answers.get("topic_prompt") == "welcome back"
        assert state.get(WizardKeys.CURRENT_STEP) == "topic"
    finally:
        engine.shutdown()
        runtime.stop()
        clear_palm_runtime()