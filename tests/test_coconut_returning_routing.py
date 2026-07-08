"""Returning coconut-npc travelers skip reputation and get tailored topic copy."""

from __future__ import annotations

from examples.definitions.coconut_npc import (
    COCONUT_NPC_FLOW,
    RETURNING_TOPIC_BY_REPUTATION,
)
from examples.definitions.coconut_resources import LOAD_COCONUT_PLAYER, SAVE_COCONUT_PLAYER
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
from palm.patterns.wizard.flow.phases._base import provide_wizard_input
from palm.providers.kv.provider import KvProvider
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


def _tree_and_engine():
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
    return root, runtime, engine


def _seed_returning_friend() -> None:
    provider = KvProvider(name="kv")
    provider.invoke(
        "put",
        resource_id="players/Gruber",
        params={
            "namespace": "coconut",
            "backend": "memory",
            "value": {
                "visit_count": 1,
                "reputation": "friend",
                "player_name": "Gruber",
                "coconuts_owned": 1,
                "last_topic": "rumors",
            },
        },
    )


def test_returning_traveler_skips_reputation_and_uses_friend_topic_prompt() -> None:
    _seed_returning_friend()
    root, runtime, engine = _tree_and_engine()
    state = BlackboardState()
    try:
        assert root.tick(state).name == "WAITING_FOR_INPUT"
        provide_wizard_input(state, "Gruber")
        for _ in range(80):
            slug = state.get(WizardKeys.CURRENT_STEP)
            if slug == "topic":
                break
            if slug == "reputation":
                raise AssertionError("returning player should not see reputation step")
            root.tick(state)
        else:
            raise AssertionError(f"expected topic step, got {state.get(WizardKeys.CURRENT_STEP)!r}")

        answers = state.get(WizardKeys.ANSWERS) or {}
        assert answers.get("reputation") == "friend"
        assert "sweet coconuts" in str(answers.get("mood_line") or "").lower()
        assert answers.get("topic_prompt") == RETURNING_TOPIC_BY_REPUTATION["friend"]

        prompt = state.get(WizardKeys.ACTIVE_PROMPT)
        assert isinstance(prompt, dict)
        body = str(prompt.get("prompt") or "")
        assert "welcome back" in body.lower()
        assert "friend" in body.lower()
    finally:
        engine.shutdown()
        runtime.stop()
        clear_palm_runtime()