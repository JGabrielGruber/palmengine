"""Unit tests for DefinitionService catalog write methods."""

from __future__ import annotations

import pytest

from palm.common.cqrs import CommandBus
from palm.common.cqrs.query import GetFlowQuery, ListFlowsQuery
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.definitions import FlowDefinition
from palm.services.definitions import DefinitionService


class _QueryBus:
    def __init__(self, repository: DefinitionRepository) -> None:
        self._repository = repository

    def register(self, query_type: type, handler: object) -> None:
        return None

    def ask(self, query: object) -> object:
        if isinstance(query, GetFlowQuery):
            try:
                return self._repository.get_flow(query.flow_id)
            except Exception:
                return None
        if isinstance(query, ListFlowsQuery):
            flows = self._repository.list_flows()
            if query.pattern:
                return [flow for flow in flows if flow.pattern == query.pattern]
            return flows
        raise AssertionError(f"unexpected query: {query!r}")


@pytest.fixture
def service() -> DefinitionService:
    repository = DefinitionRepository()
    queries = _QueryBus(repository)
    return DefinitionService(
        commands=CommandBus(),
        queries=queries,
        schemas=CqrsSchemaRegistry(),
        repository=repository,
    )


def test_definition_service_create_and_delete_flow(service: DefinitionService) -> None:
    created = service.create_flow(
        {
            "name": "svc-flow",
            "pattern": "wizard",
            "options": {"steps": [{"slug": "a", "title": "A", "prompt": "A?"}]},
        }
    )
    assert created["name"] == "svc-flow"

    row = service.get_flow("svc-flow", verbose=False)
    assert row["flow_id"] == "svc-flow"

    assert service.delete_flow("svc-flow") is True

    with pytest.raises(DefinitionNotFoundServiceError):
        service.get_flow("svc-flow")


def test_definition_service_update_flow(service: DefinitionService) -> None:
    service._repository.register_flow(
        FlowDefinition(name="upd-flow", pattern="wizard", options={"steps": []}),
    )
    updated = service.update_flow(
        "upd-flow",
        {
            "name": "upd-flow",
            "pattern": "wizard",
            "options": {"steps": [{"slug": "b", "title": "B", "prompt": "B?"}]},
        },
    )
    assert updated["options"]["steps"][0]["slug"] == "b"