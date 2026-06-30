"""Tests for ResourceLeaf and wizard resource steps."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource import build_resource_leaf, resource_definition_resolver
from palm.core.behavior_tree import PatternStatus, ResourceLeaf
from palm.core.resource import ResourceEngine
from palm.definitions import ResourceDefinition
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.pattern import WizardPattern
from palm.states import BlackboardState


def _fetch_customer_definition(*, base_url: str) -> ResourceDefinition:
    return ResourceDefinition(
        id="resource-fetch-customer",
        name="fetch-customer",
        provider="rest",
        action="fetch",
        resource_id="customers/{customer_id}",
        params={"customer_id": "{{ state.customer_id }}", "base_url": base_url},
    )


def _resource_engine_with_repo(base_url: str) -> ResourceEngine:
    repo = DefinitionRepository()
    repo.register_resource(_fetch_customer_definition(base_url=base_url))
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    return engine


def test_resource_leaf_direct_provider(rest_base_url: str) -> None:
    engine = ResourceEngine()
    engine.initialize()
    leaf = build_resource_leaf(
        "health-check",
        resource_engine=engine,
        provider="rest",
        action="fetch",
        resource_id="health/check",
        params={"base_url": rest_base_url},
        output_key="health",
    )
    state = BlackboardState()
    assert leaf.tick(state) == PatternStatus.SUCCESS
    assert state.get("health")["body"]["ok"] is True
    engine.shutdown()


def test_resource_leaf_definition_ref_with_state_binding(rest_base_url: str) -> None:
    engine = _resource_engine_with_repo(rest_base_url)
    leaf = build_resource_leaf(
        "get-customer",
        resource_engine=engine,
        resource_ref="fetch-customer",
        output_key="customer_data",
    )
    state = BlackboardState({"customer_id": "cust-77"})
    assert leaf.tick(state) == PatternStatus.SUCCESS
    assert state.get("customer_data")["id"] == "customers/cust-77"
    trace = state.get(leaf.trace_key)
    assert isinstance(trace, dict) and trace["success"] is True
    engine.shutdown()


def test_resource_leaf_failure_sets_error_key() -> None:
    engine = ResourceEngine()
    engine.initialize()
    leaf = ResourceLeaf(
        "bad-action",
        resource_engine=engine,
        provider="rest",
        action="unknown",
        error_key="resource_error",
    )
    state = BlackboardState()
    assert leaf.tick(state) == PatternStatus.FAILURE
    assert state.get("resource_error") is not None
    engine.shutdown()


def test_resource_leaf_requires_ref_or_provider() -> None:
    with pytest.raises(ValueError, match="resource_ref or provider"):
        ResourceLeaf("orphan")


def test_wizard_resource_step_invokes_definition(rest_base_url: str) -> None:
    engine = _resource_engine_with_repo(rest_base_url)
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="customer_id",
                title="Customer ID",
                prompt="Customer id?",
            ),
            WizardStepConfig(
                slug="get-customer",
                title="Load Customer",
                prompt="Loading customer",
                step_kind="resource",
                resource_ref="fetch-customer",
                params={"customer_id": "{{ state.customer_id }}"},
                output_key="customer_data",
            ),
        ),
    )
    wizard = WizardPattern(name="resource-wizard", config=config, resource_engine=engine)
    state = BlackboardState()

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "cust-88")
    assert wizard.tick(state) == PatternStatus.SUCCESS

    answers = state.get(WizardKeys.ANSWERS)
    assert answers["customer_id"] == "cust-88"
    assert answers["customer_data"]["id"] == "customers/cust-88"
    assert state.get(f"{WizardKeys.RESOURCE_RESULT}:get-customer") is not None
    engine.shutdown()


def test_resource_leaf_trace_includes_ref_and_action(rest_base_url: str) -> None:
    engine = _resource_engine_with_repo(rest_base_url)
    leaf = build_resource_leaf(
        "get-customer",
        resource_engine=engine,
        resource_ref="fetch-customer",
        output_key="customer_data",
    )
    state = BlackboardState({"customer_id": "cust-1"})
    leaf.tick(state)
    trace = state.get(leaf.trace_key)
    assert trace["resource_ref"] == "fetch-customer"
    assert trace["action"] == "fetch"
    assert trace["success"] is True
    engine.shutdown()


def test_resource_leaf_failure_message_includes_ref_and_action() -> None:
    engine = ResourceEngine()
    engine.initialize()
    leaf = ResourceLeaf(
        "bad-action",
        resource_engine=engine,
        resource_ref="fetch-customer",
        action="unknown",
        error_key="resource_error",
    )
    state = BlackboardState()
    leaf.tick(state)
    error = state.get("resource_error")
    assert "fetch-customer" in error
    assert "action=unknown" in error
    engine.shutdown()
