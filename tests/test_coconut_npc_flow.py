"""Tests for coconut-npc reference flow — branching, transforms, routing."""

from __future__ import annotations

from examples.definitions.coconut_npc import COCONUT_NPC_FLOW
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
from palm.patterns.wizard.bindings.design import validate_wizard_design_proposal


def test_coconut_npc_flow_builds() -> None:
    options = parse_wizard_flow_options(COCONUT_NPC_FLOW.options)
    config = wizard_config_from_options(options)
    slugs = [step.slug for step in config.steps]
    assert slugs[0] == "player_name"
    assert "load_player" in slugs
    assert "unwrap_profile" in slugs
    assert "reputation_gate" in slugs
    assert "topic" in slugs
    assert "build_greeting" in slugs
    assert "save_profile" in slugs
    assert config.steps[slugs.index("topic")].params is not None
    route = config.steps[slugs.index("topic")].params.get("route_on_answer")
    assert isinstance(route, dict)
    assert route.get("rumors") == "rumors"
    assert route.get("leave") == "farewell"


def test_coconut_npc_design_proposal_validates() -> None:
    body = {
        "name": "coconut-npc",
        "pattern": "wizard",
        "options": COCONUT_NPC_FLOW.options,
    }
    valid, blockers = validate_wizard_design_proposal(body, None)
    assert blockers == [], blockers
    assert valid is True


def test_coconut_npc_transform_steps_without_nested_wrapper() -> None:
    """Flat transform steps (repo canonical) must pass design contributor."""
    steps = COCONUT_NPC_FLOW.options["steps"]
    transform_steps = [s for s in steps if s.get("step_kind") == "transform"]
    assert len(transform_steps) >= 2
    for step in transform_steps:
        assert "transform" not in step or step.get("rule")
        assert step.get("source_key")
        assert step.get("rule")