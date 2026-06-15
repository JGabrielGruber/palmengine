"""Tests for wizard transform steps and string_format integration."""

from __future__ import annotations

import pytest

from palm.common.patterns import build_pattern
from palm.common.transforms import TransformExecutor, autoload
from palm.core import PatternStatus
from palm.core.transform.registry import transform_registry
from palm.definitions import FlowDefinition
from palm.patterns.wizard import WizardKeys, WizardPattern
from palm.patterns.wizard.builder import wizard_config_from_options
from palm.patterns.wizard.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.transform_leaf import default_transform_prompt
from tests.core.fakes import TestState


@pytest.fixture
def executor() -> TransformExecutor:
    transform_registry.clear()
    autoload()
    return TransformExecutor()


def _transform_wizard_config() -> WizardConfig:
    return wizard_config_from_options(
        {
            "steps": [
                {
                    "slug": "name",
                    "title": "Name",
                    "prompt": "Enter your name",
                },
                {
                    "slug": "format_greeting",
                    "step_kind": "transform",
                    "source_key": "name",
                    "target_key": "greeting",
                    "rule": "string_format",
                    "options": {"template": "Hello, {value}!", "case": "title"},
                },
                {
                    "slug": "role",
                    "title": "Role",
                    "prompt": "Pick a role",
                    "field_type": "choice",
                    "choices": ["developer", "manager"],
                },
            ],
        },
    )


def test_wizard_transform_step_builds_from_options() -> None:
    config = _transform_wizard_config()
    step = config.get_step("format_greeting")
    assert step is not None
    assert step.step_kind == "transform"
    assert step.transform is not None
    assert step.transform.rule == "string_format"
    assert step.transform.source_key == "name"
    assert step.transform.target_key == "greeting"
    assert "string_format" in step.prompt


def test_wizard_transform_runs_between_input_steps() -> None:
    transform_registry.clear()
    autoload()
    wizard = WizardPattern(name="w", config=_transform_wizard_config())
    state = TestState()

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "ada lovelace")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT

    assert state.get("greeting") == "Hello, Ada Lovelace!"
    assert wizard.answers(state)["greeting"] == "Hello, Ada Lovelace!"
    assert state.get(WizardKeys.TRANSFORM_FEEDBACK) is not None

    wizard.provide_input(state, "developer")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state) == {
        "name": "ada lovelace",
        "greeting": "Hello, Ada Lovelace!",
        "role": "developer",
    }


def test_wizard_transform_failure_publishes_validation_feedback() -> None:
    config = wizard_config_from_options(
        {
            "steps": [
                {"slug": "name", "prompt": "Name"},
                {
                    "slug": "bad_transform",
                    "step_kind": "transform",
                    "source_key": "missing_key",
                    "rule": "string_format",
                    "options": {"template": "Hi {value}"},
                },
            ],
        },
    )
    wizard = WizardPattern(name="w", config=config)
    state = TestState()

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    assert wizard.tick(state) == PatternStatus.FAILURE
    assert state.get(WizardKeys.VALIDATION_ERROR) is not None
    assert wizard.current_step_slug(state) == "bad_transform"


def test_wizard_transform_chain() -> None:
    transform_registry.clear()
    autoload()
    config = wizard_config_from_options(
        {
            "steps": [
                {"slug": "seed", "prompt": "Continue"},
                {
                    "slug": "normalize",
                    "step_kind": "transform",
                    "source_key": "raw",
                    "target_key": "clean",
                    "chain": ["map_fields", "rename_field"],
                    "options_by_rule": {
                        "map_fields": {
                            "mapping": {"first_name": "given"},
                            "keep_unmapped": False,
                        },
                        "rename_field": {"from_key": "given", "to_key": "name"},
                    },
                },
            ],
        },
    )
    wizard = WizardPattern(name="w", config=config)
    state = TestState()
    state.set("raw", {"first_name": "Ada", "ignored": True})

    wizard.tick(state)
    wizard.provide_input(state, "ok")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert state.get("clean") == {"name": "Ada"}
    assert wizard.answers(state)["clean"] == {"name": "Ada"}


def test_string_format_rule_cases(executor: TransformExecutor) -> None:
    result = executor.apply("string_format", "hello world", case="title")
    assert result.value == "Hello World"

    result = executor.apply(
        "string_format",
        {"name": "ada"},
        field="name",
        template="Hi {name}!",
    )
    assert result.value == "Hi ada!"

    result = executor.apply(
        "string_format",
        "2026-06-15",
        date_format="%B %d, %Y",
    )
    assert result.value == "June 15, 2026"


def test_string_format_template_missing_key(executor: TransformExecutor) -> None:
    from palm.core import TransformApplicationError

    with pytest.raises(TransformApplicationError, match="missing key"):
        executor.apply("string_format", "Ada", template="Hello {missing}!")


def test_transform_example_flow_builds() -> None:
    from examples.definitions.transform_example import TRANSFORM_EXAMPLE_FLOW

    flow = TRANSFORM_EXAMPLE_FLOW
    built = build_pattern(flow)
    assert isinstance(built, WizardPattern)
    assert built.config.get_step("format_greeting") is not None


def test_default_transform_prompt_uses_chain() -> None:
    from palm.common.transforms.builder import TransformStepSpec

    step = WizardStepConfig(
        slug="normalize",
        title="Normalize",
        prompt="run",
        step_kind="transform",
        transform=TransformStepSpec(
            name="normalize",
            source_key="raw",
            target_key="clean",
            chain=("map_fields", "rename_field"),
        ),
    )
    prompt = default_transform_prompt(step)
    assert "map_fields → rename_field" in prompt
    assert "raw → clean" in prompt