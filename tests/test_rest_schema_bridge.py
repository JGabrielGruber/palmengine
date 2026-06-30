"""REST schema bridge — project CQRS registry schemas onto HTTP bodies."""

from __future__ import annotations

import palm.patterns  # noqa: F401
from palm.common.cqrs.command import ProvideInputCommand
from palm.common.cqrs.schemas import build_schema_registry
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from palm.runtimes.server.surfaces.rest.schema_bridge import body_schema_for_command


def test_body_schema_for_wizard_input_value_only() -> None:
    registry = build_schema_registry()
    schema = body_schema_for_command(
        registry,
        ProvideWizardInputCommand,
        properties=("value",),
    )
    assert schema.validate_state({"value": "yes"}) == []
    assert schema.validate_state({}) != []


def test_body_schema_for_provide_input_command() -> None:
    registry = build_schema_registry()
    schema = body_schema_for_command(
        registry,
        ProvideInputCommand,
        properties=("value",),
    )
    assert schema.validate_state({"value": 42}) == []
    assert schema.validate_state({}) != []


def test_body_schema_for_wizard_backtrack_to_step() -> None:
    registry = build_schema_registry()
    schema = body_schema_for_command(
        registry,
        RequestWizardBacktrackCommand,
        properties=("to_step",),
    )
    assert schema.validate_state({"to_step": "confirm"}) == []
    assert schema.validate_state({}) == []