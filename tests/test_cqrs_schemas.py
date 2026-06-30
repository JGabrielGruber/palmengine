"""Tests for CQRS schema registry."""

from __future__ import annotations

from dataclasses import dataclass

import palm.patterns  # noqa: F401
from palm.common.cqrs.command import Command, SubmitFlowCommand
from palm.common.cqrs.schemas import CqrsSchemaRegistry, ValidationResult, build_schema_registry
from palm.core.context.state_schema import DictStateSchema
from palm.patterns._registry import (
    CqrsContributor,
    clear_cqrs_contributors,
    register_cqrs_contributor,
    restore_cqrs_contributors,
    snapshot_cqrs_contributors,
)
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    SubmitWizardCommand,
)


@dataclass(frozen=True)
class _SampleCommand(Command):
    name: str
    count: int = 1


_SAMPLE_SCHEMA = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "count": {"type": "integer", "minimum": 1},
        },
        "required": ["name"],
    }
)


def test_registry_register_and_lookup() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    assert registry.schema_for(_SampleCommand) is _SAMPLE_SCHEMA
    assert registry.schema_for(str) is None


def test_registry_validate_dataclass_as_dict() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    result = registry.validate(_SampleCommand(name="demo"))
    assert result.ok is True
    assert result.errors == []


def test_registry_validate_rejects_invalid() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    result = registry.validate(_SampleCommand(name="", count=0))
    assert result.ok is False
    assert len(result.errors) >= 1
    assert result.details[0]["field"]


def test_core_submit_flow_command_has_schema() -> None:
    registry = build_schema_registry()
    schema = registry.schema_for(SubmitFlowCommand)
    assert schema is not None
    result = registry.validate(SubmitFlowCommand(flow="demo"))
    assert result.ok is True


def test_wizard_commands_have_schemas() -> None:
    registry = build_schema_registry()
    assert registry.schema_for(SubmitWizardCommand) is not None
    assert registry.schema_for(ProvideWizardInputCommand) is not None


def test_registry_collects_contributor_schemas() -> None:
    saved = snapshot_cqrs_contributors()
    try:
        clear_cqrs_contributors()

        @dataclass(frozen=True)
        class _PatCmd(Command):
            slug: str

        schema = DictStateSchema(
            {
                "type": "object",
                "properties": {"slug": {"type": "string", "minLength": 1}},
                "required": ["slug"],
            }
        )
        register_cqrs_contributor(
            CqrsContributor(
                pattern_name="_test_pattern",
                command_types=(_PatCmd,),
                command_schemas={_PatCmd: schema},
            )
        )
        registry = build_schema_registry()
        assert registry.schema_for(_PatCmd) is schema
        result = registry.validate(_PatCmd(slug=""))
        assert isinstance(result, ValidationResult)
        assert result.ok is False
    finally:
        restore_cqrs_contributors(saved)