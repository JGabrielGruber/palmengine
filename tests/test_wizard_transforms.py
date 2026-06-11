"""Wizard integration tests for resource + transform steps."""

from __future__ import annotations

from typing import Any

import pytest

from palm.common.transforms import TransformPipeline
from palm.core.behavior_tree import PatternStatus
from palm.core.registry import provider_registry
from palm.core.resource import BaseProvider, ResourceEngine
from palm.core.transform import TransformEngine
from palm.patterns.wizard import WizardConfig, WizardKeys, WizardPattern, WizardStepConfig
from palm.states import BlackboardState


class _RoleRowsProvider(BaseProvider):
    def connect(self) -> None:
        return None

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return [
            {"id": "dev", "label": "Developer", "active": True},
            {"id": "mgr", "label": "Manager", "active": True},
            {"id": "oth", "label": "Other", "active": False},
        ]

    def disconnect(self) -> None:
        return None


@pytest.fixture
def role_provider_registered() -> None:
    import palm.providers  # noqa: F401 — ensure built-in providers stay registered

    provider_registry.register("role_rows", _RoleRowsProvider)
    yield


def test_wizard_choice_step_from_resource_transform(role_provider_registered: None) -> None:
    pipeline = TransformPipeline.parse(
        {
            "chain": [
                {"rule": "filter_list", "field": "active", "equals": True},
                {
                    "rule": "map_list",
                    "sub_rule": "pick_fields",
                    "sub_options": {"fields": ["id", "label"]},
                },
            ]
        }
    )
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Select your role",
                field_type="choice",
                resource_provider="role_rows",
                resource_id="roles",
                transform=pipeline,
                choices_label_key="label",
            ),
        )
    )
    resource = ResourceEngine()
    resource.initialize()
    transform = TransformEngine()
    transform.initialize()
    state = BlackboardState()
    wizard = WizardPattern(
        name="roles",
        config=config,
        resource_engine=resource,
        transform_engine=transform,
    )

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    prompt = state.get(WizardKeys.ACTIVE_PROMPT)
    assert prompt is not None
    assert prompt["choices"] == ["Developer", "Manager"]

    wizard.provide_input(state, "Developer")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["role"] == "Developer"
    transformed = state.get(f"{WizardKeys.TRANSFORM_RESULT}:role")
    assert transformed == [
        {"id": "dev", "label": "Developer"},
        {"id": "mgr", "label": "Manager"},
    ]

    resource.shutdown()
    transform.shutdown()


class _LookupProvider(BaseProvider):
    def connect(self) -> None:
        return None

    def fetch(self, resource_id: str, **params: Any) -> Any:
        return {"id": resource_id, "source": "lookup", "noise": True}

    def disconnect(self) -> None:
        return None


def test_wizard_action_applies_transform(role_provider_registered: None) -> None:
    provider_registry.register("lookup", _LookupProvider)
    pipeline = TransformPipeline.parse({"rule": "pick_fields", "fields": ["id", "source"]})
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="lookup",
                title="Lookup",
                prompt="Fetch?",
                step_kind="action",
                field_type="confirm",
                resource_provider="lookup",
                resource_id="users/1",
                transform=pipeline,
            ),
        ),
    )
    resource = ResourceEngine()
    resource.initialize()
    transform = TransformEngine()
    transform.initialize()
    state = BlackboardState()
    wizard = WizardPattern(
        name="w",
        config=config,
        resource_engine=resource,
        transform_engine=transform,
    )
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    result = state.get(f"{WizardKeys.TRANSFORM_RESULT}:lookup")
    assert result == {"id": "users/1", "source": "lookup"}

    resource.shutdown()
    transform.shutdown()


def test_builder_parses_transform_block() -> None:
    from palm.patterns.wizard.builder import wizard_config_from_options

    config = wizard_config_from_options(
        {
            "steps": [
                {
                    "slug": "role",
                    "field_type": "choice",
                    "resource_provider": "role_rows",
                    "resource_id": "roles",
                    "transform": {
                        "rule": "filter_list",
                        "field": "active",
                        "equals": True,
                    },
                }
            ]
        }
    )
    step = config.steps[0]
    assert step.transform is not None
    assert step.transform.steps[0].rule == "filter_list"