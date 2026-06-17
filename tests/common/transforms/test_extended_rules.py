"""Tests for extended built-in transform rules (0.9 final)."""

from __future__ import annotations

import pytest

from palm.common.transforms import TransformExecutor, autoload
from palm.core import TransformApplicationError
from palm.core.resource import ResourceEngine
from palm.core.transform.registry import transform_registry


@pytest.fixture
def executor() -> TransformExecutor:
    transform_registry.clear()
    autoload()
    return TransformExecutor()


def test_jsonpath_extract_and_set(executor: TransformExecutor) -> None:
    payload = {"user": {"name": "Ada"}, "items": [{"id": "a"}]}
    extracted = executor.apply("jsonpath_extract", payload, path="user.name")
    assert extracted.value == "Ada"

    updated = executor.apply(
        "jsonpath_set",
        payload,
        path="user.role",
        set_value="developer",
    )
    assert updated.value == {"user": {"name": "Ada", "role": "developer"}, "items": [{"id": "a"}]}


def test_calculate_expression(executor: TransformExecutor) -> None:
    result = executor.apply(
        "calculate",
        {"price": 10, "qty": 3, "discount": 0.1},
        expression="price * qty * (1 - discount)",
    )
    assert result.value == pytest.approx(27.0)


def test_lookup_with_default(executor: TransformExecutor) -> None:
    result = executor.apply(
        "lookup",
        "manager",
        table={"developer": "Engineering", "manager": "Leadership"},
    )
    assert result.value == "Leadership"

    fallback = executor.apply(
        "lookup",
        "unknown",
        table={"a": 1},
        default="n/a",
    )
    assert fallback.value == "n/a"


def test_conditional_then_else(executor: TransformExecutor) -> None:
    result = executor.apply(
        "conditional",
        {"status": "active", "score": 10},
        field="status",
        equals="active",
        then="approved",
        **{"else": "rejected"},
    )
    assert result.value == "approved"

    result = executor.apply(
        "conditional",
        {"status": "inactive"},
        field="status",
        equals="active",
        then="approved",
        **{"else": "rejected"},
    )
    assert result.value == "rejected"


def test_date_format_and_parse(executor: TransformExecutor) -> None:
    formatted = executor.apply("date_format", "2026-06-15", format="%B %d, %Y")
    assert formatted.value == "June 15, 2026"

    parsed = executor.apply("date_parse", "15/06/2026", input_format="%d/%m/%Y")
    assert parsed.value == "2026-06-15"


def test_enrich_resource_via_resource_ref(executor: TransformExecutor) -> None:
    import palm.providers  # noqa: F401

    from palm.common import DefinitionRepository
    from palm.common.resource import resource_definition_resolver
    from palm.definitions import ResourceDefinition

    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            name="check-health",
            provider="rest",
            action="fetch",
            resource_id="health/check",
        )
    )
    resource = ResourceEngine()
    resource.initialize(definition_resolver=resource_definition_resolver(repo))
    try:
        result = executor.apply(
            "enrich_resource",
            {"tenant": "acme"},
            resource_ref="check-health",
            resource_engine=resource,
        )
        assert result.value["tenant"] == "acme"
        assert result.value["resource"]["source"] == "rest"
    finally:
        resource.shutdown()


def test_enrich_resource_merges_fetch(executor: TransformExecutor) -> None:
    import palm.providers  # noqa: F401

    resource = ResourceEngine()
    resource.initialize()
    try:
        result = executor.apply(
            "enrich_resource",
            {"id": "users/42", "name": "Ada"},
            provider="rest",
            resource_engine=resource,
        )
        assert result.value["name"] == "Ada"
        assert result.value["resource"]["id"] == "users/42"
        assert result.value["resource"]["source"] == "rest"
    finally:
        resource.shutdown()


def test_conditional_numeric_compare(executor: TransformExecutor) -> None:
    result = executor.apply("conditional", 50, gt=40, then="large", **{"else": "standard"})
    assert result.value == "large"

    result = executor.apply("conditional", 10, gt=40, then="large", **{"else": "standard"})
    assert result.value == "standard"


def test_conditional_requires_predicate(executor: TransformExecutor) -> None:
    with pytest.raises(TransformApplicationError, match="predicate"):
        executor.apply("conditional", {"x": 1}, field="x", then="yes", **{"else": "no"})
