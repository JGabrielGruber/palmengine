"""Definition service — catalog of flows, processes, and resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery, GetProcessQuery, ListFlowsQuery, ListProcessesQuery
from palm.common.exceptions import DefinitionNotFoundError
from palm.common.resource.catalog import ResourceCatalog
from palm.common.runtimes.server.plans import prepare_flow_from_body
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.common.services.views import (
    flow_detail,
    flow_step_slugs,
    flow_summary,
    process_detail,
    process_summary,
    resource_summary,
)
from palm.definitions.flow import FlowDefinition

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
        return [flow_summary(flow) for flow in flows]

    def get_flow(self, flow_id: str, *, verbose: bool = True) -> dict[str, Any]:
        flow = self.ask(GetFlowQuery(flow_id=flow_id))
        if flow is None:
            raise DefinitionNotFoundServiceError("flow", flow_id)
        return flow_detail(flow) if verbose else flow_summary(flow)

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
        return [process_summary(process) for process in processes]

    def get_process(self, process_id: str) -> dict[str, Any]:
        process = self.ask(GetProcessQuery(process_id=process_id))
        if process is None:
            raise DefinitionNotFoundServiceError("process", process_id)
        return process_detail(process)

    def list_resources(self, *, provider: str | None = None) -> list[dict[str, Any]]:
        catalog = ResourceCatalog(self._repository)
        rows = [resource_summary(entry) for entry in catalog.entries()]
        if provider:
            rows = [row for row in rows if row.get("provider") == provider]
        return rows

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        catalog = ResourceCatalog(self._repository)
        try:
            return catalog.describe(resource_ref)
        except DefinitionNotFoundError as exc:
            raise DefinitionNotFoundServiceError("resource", resource_ref) from exc


__all__ = ["DefinitionService"]