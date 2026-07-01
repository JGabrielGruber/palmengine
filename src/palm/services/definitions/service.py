"""Definition service — catalog of flows, processes, and resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery, GetProcessQuery, ListFlowsQuery, ListProcessesQuery
from palm.common.exceptions import DefinitionNotFoundError
from palm.common.resource.catalog import ResourceCatalog
from palm.common.runtimes.server.plans import prepare_flow_from_body
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.definitions.flow import FlowDefinition
from palm.patterns.wizard.bindings.catalog import flow_step_slugs
from palm.services.definitions.flows import flow_catalog_row
from palm.services.definitions.parsers import parse_flow, parse_process, parse_resource
from palm.services.definitions.processes import process_catalog_row
from palm.services.definitions.resources import resource_catalog_row

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.common.runtimes.base import BaseRuntime


class DefinitionService(BaseService):
    """User definition catalog — composes CQRS and the resource catalog."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        repository: DefinitionRepository,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._repository = repository

    def list_flows(self, *, pattern: str | None = None) -> list[dict[str, Any]]:
        flows = self.ask(ListFlowsQuery(pattern=pattern))
        return [flow_catalog_row(flow) for flow in flows]

    def get_flow(self, flow_id: str, *, verbose: bool = True) -> dict[str, Any]:
        flow = self.ask(GetFlowQuery(flow_id=flow_id))
        if flow is None:
            raise DefinitionNotFoundServiceError("flow", flow_id)
        return flow.to_dict() if verbose else flow_catalog_row(flow)

    def validate_flow(self, body: dict[str, Any], *, runtime: BaseRuntime) -> dict[str, Any]:
        """Dry-run flow definition build without submitting a job."""
        plan = prepare_flow_from_body(runtime, body)
        pattern = plan.metadata.get("pattern") or body.get("flow", {}).get("pattern")
        flow_name = plan.metadata.get("flow") or plan.metadata.get("flow_name")
        step_slugs: list[str] = []
        flow_def = plan.metadata.get("flow_definition")
        if isinstance(flow_def, dict):
            step_slugs = flow_step_slugs(FlowDefinition.from_dict(flow_def))
        return {
            "valid": True,
            "pattern": pattern,
            "flow": flow_name,
            "step_slugs": step_slugs,
        }

    def list_processes(self) -> list[dict[str, Any]]:
        processes = self.ask(ListProcessesQuery())
        return [process_catalog_row(process) for process in processes]

    def get_process(self, process_id: str) -> dict[str, Any]:
        process = self.ask(GetProcessQuery(process_id=process_id))
        if process is None:
            raise DefinitionNotFoundServiceError("process", process_id)
        return process.to_dict()

    def list_resources(self, *, provider: str | None = None) -> list[dict[str, Any]]:
        catalog = ResourceCatalog(self._repository)
        rows = [resource_catalog_row(entry) for entry in catalog.entries()]
        if provider:
            rows = [row for row in rows if row.get("provider") == provider]
        return rows

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        catalog = ResourceCatalog(self._repository)
        try:
            return catalog.describe(resource_ref)
        except DefinitionNotFoundError as exc:
            raise DefinitionNotFoundServiceError("resource", resource_ref) from exc

    def create_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        flow = parse_flow(body)
        self._repository.register_flow(flow)
        return flow.to_dict()

    def update_flow(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self.get_flow(flow_id)
        flow = parse_flow(body)
        self._repository.register_flow(flow)
        return flow.to_dict()

    def delete_flow(self, flow_id: str) -> bool:
        flow = self.ask(GetFlowQuery(flow_id=flow_id))
        if flow is None:
            raise DefinitionNotFoundServiceError("flow", flow_id)
        return self._repository.delete_flow(flow.definition_id, by_id=True)

    def create_process(self, body: dict[str, Any]) -> dict[str, Any]:
        process = parse_process(body)
        self._repository.register_process(process)
        for flow in process.flows:
            self._repository.register_flow(flow)
        return process.to_dict()

    def update_process(self, process_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self.get_process(process_id)
        process = parse_process(body)
        self._repository.register_process(process)
        for flow in process.flows:
            self._repository.register_flow(flow)
        return process.to_dict()

    def delete_process(self, process_id: str) -> bool:
        process = self.ask(GetProcessQuery(process_id=process_id))
        if process is None:
            raise DefinitionNotFoundServiceError("process", process_id)
        return self._repository.delete_process(process.definition_id, by_id=True)

    def create_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        resource = parse_resource(body)
        self._repository.register_resource(resource)
        return resource.to_dict()

    def update_resource(self, resource_ref: str, body: dict[str, Any]) -> dict[str, Any]:
        self.get_resource(resource_ref)
        resource = parse_resource(body)
        self._repository.register_resource(resource)
        return resource.to_dict()

    def delete_resource(self, resource_ref: str) -> bool:
        catalog = ResourceCatalog(self._repository)
        try:
            described = catalog.describe(resource_ref)
        except DefinitionNotFoundError as exc:
            raise DefinitionNotFoundServiceError("resource", resource_ref) from exc
        definition_id = str(described.get("definition_id") or described.get("name") or resource_ref)
        return self._repository.delete_resource(definition_id, by_id=True)


__all__ = ["DefinitionService"]