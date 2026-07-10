"""Wizard design contributor — flat transform steps and coconut-npc validation."""

from __future__ import annotations

from examples.definitions.coconut.npc import COCONUT_NPC_FLOW
from examples.definitions.transform_example import TRANSFORM_EXAMPLE_FLOW
from palm.patterns.wizard.bindings.design import (
    normalize_wizard_step,
    validate_wizard_design_proposal,
)


def test_transform_example_design_validates() -> None:
    body = {
        "name": "transform-example",
        "pattern": "wizard",
        "options": TRANSFORM_EXAMPLE_FLOW.options,
    }
    valid, blockers = validate_wizard_design_proposal(body, None)
    assert blockers == []
    assert valid is True


def test_nested_transform_normalizes_for_validation() -> None:
    step = {
        "slug": "fmt",
        "step_kind": "transform",
        "transform": {
            "source_key": "name",
            "target_key": "greeting",
            "rule": "string_format",
            "options": {"template": "Hi {value}"},
        },
    }
    normalized = normalize_wizard_step(step)
    assert normalized["rule"] == "string_format"
    assert normalized["source_key"] == "name"
    body = {
        "name": "nested-transform-demo",
        "pattern": "wizard",
        "options": {"steps": [step]},
    }
    valid, blockers = validate_wizard_design_proposal(body, None)
    assert blockers == []
    assert valid is True


def test_coconut_npc_design_validates() -> None:
    body = {
        "name": "coconut-npc",
        "pattern": "wizard",
        "options": COCONUT_NPC_FLOW.options,
    }
    valid, blockers = validate_wizard_design_proposal(body, None)
    assert blockers == []
    assert valid is True