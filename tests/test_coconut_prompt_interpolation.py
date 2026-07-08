"""Integration test — coconut-npc topic prompt shows mood_line after reputation step."""

from __future__ import annotations

from examples.definitions.coconut_npc import COCONUT_NPC_FLOW
from examples.definitions.coconut_resources import (
    LOAD_COCONUT_PLAYER,
    SAVE_COCONUT_PLAYER,
)
from examples.definitions.coconut_transforms import register_coconut_transforms
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
from palm.patterns.wizard.flow.phases._base import provide_wizard_input
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


def _wizard_tree():
    register_coconut_transforms()
    repo = DefinitionRepository()
    repo.register_resource(LOAD_COCONUT_PLAYER)
    repo.register_resource(SAVE_COCONUT_PLAYER)
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    runtime = EmbeddedRuntime()
    runtime.start()
    bind_palm_runtime(runtime)
    options = parse_wizard_flow_options(COCONUT_NPC_FLOW.options)
    config = wizard_config_from_options(options)
    root, _sequence = build_wizard_tree("coconut-npc", config, resource_engine=engine)
    return root, runtime


def test_topic_prompt_includes_mood_line_after_friend_reputation() -> None:
    root, runtime = _wizard_tree()
    state = BlackboardState()

    assert root.tick(state).name == "WAITING_FOR_INPUT"
    provide_wizard_input(state, "Lyra")
    while state.get(WizardKeys.CURRENT_STEP) != "reputation":
        status = root.tick(state)
        if status.name == "WAITING_FOR_INPUT":
            slug = state.get(WizardKeys.CURRENT_STEP)
            if slug == "reputation":
                break
            provide_wizard_input(state, "placeholder")

    provide_wizard_input(state, "friend")
    while state.get(WizardKeys.CURRENT_STEP) != "topic":
        status = root.tick(state)
        if status.name == "WAITING_FOR_INPUT" and state.get(WizardKeys.CURRENT_STEP) == "topic":
            break

    prompt = state.get(WizardKeys.ACTIVE_PROMPT)
    assert isinstance(prompt, dict)
    assert "sweet coconuts" in str(prompt.get("prompt", "")).lower()
    runtime.stop()
    clear_palm_runtime()