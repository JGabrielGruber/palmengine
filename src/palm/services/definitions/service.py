"""Definition service — catalog of flows, processes, and resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import MigrateInstanceCommand
from palm.common.cqrs.query import (
    AnalyzeDefinitionImpactQuery,
    GetFlowQuery,
    GetProcessQuery,
    ListFlowsQuery,
    ListProcessesQuery,
)
from palm.common.exceptions import DefinitionNotFoundError, InstanceMigrationError, InstanceNotFoundError
from palm.common.resource.catalog import ResourceCatalog
from palm.common.runtimes.server.plans import prepare_flow_from_body
from palm.common.services.base import BaseService
from palm.common.services.errors import (
    DefinitionNotFoundServiceError,
    InstanceMigrationServiceError,
    InstanceNotFoundServiceError,
)
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

    def list_flow_definitions(self) -> list[FlowDefinition]:
        """Return full flow definitions for impact scans and integrators."""
        return list(self._repository.list_flows())

    def get_flow(
        self,
        flow_id: str,
        *,
        verbose: bool = True,
        revision: int | None = None,
    ) -> dict[str, Any]:
        if revision is not None:
            try:
                flow = self._repository.get_flow(flow_id, revision=revision)
            except DefinitionNotFoundError as exc:
                raise DefinitionNotFoundServiceError("flow", flow_id) from exc
        else:
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
        published = self._repository.publish_flow_revision(flow)
        return published.to_dict()

    def update_flow(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self.get_flow(flow_id)
        flow = parse_flow(body)
        published = self._repository.publish_flow_revision(flow)
        return published.to_dict()

    def publish_flow_revision(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Append a new revision for an existing flow."""
        self.get_flow(flow_id)
        flow = parse_flow(body)
        published = self._repository.publish_flow_revision(flow)
        return published.to_dict()

    def list_flow_revisions(self, flow_id: str) -> list[dict[str, Any]]:
        """Return revision index rows for ``flow_id``."""
        return self._repository.list_flow_revisions(flow_id)

    def get_latest_revision(self, flow_id: str) -> int | None:
        """Return the latest published revision for ``flow_id``, if any."""
        return self._repository.get_latest_revision(flow_id)

    def next_revision_for_flow(self, flow_id: str) -> int:
        """Return the revision number the next publish would assign."""
        latest = self._repository.get_latest_revision(flow_id)
        if latest is not None:
            return latest + 1
        try:
            flow = self._repository.get_flow(flow_id)
        except DefinitionNotFoundError:
            return 1
        return int(flow.revision or 1) + 1

    def analyze_impact(
        self,
        flow_id: str,
        *,
        target_revision: int | None = None,
    ) -> dict[str, Any]:
        """Report instances pinned behind ``target_revision`` (latest by default)."""
        try:
            return self.ask(
                AnalyzeDefinitionImpactQuery(
                    flow_id=flow_id,
                    target_revision=target_revision,
                )
            )
        except DefinitionNotFoundError as exc:
            raise DefinitionNotFoundServiceError("flow", flow_id) from exc

    def migrate_instance(
        self,
        instance_id: str,
        *,
        target_revision: int,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Dry-run or apply a definition migration for a durable instance."""
        try:
            result = self.dispatch(
                MigrateInstanceCommand(
                    instance_id=instance_id,
                    target_revision=target_revision,
                    dry_run=dry_run,
                )
            )
        except InstanceNotFoundError as exc:
            raise InstanceNotFoundServiceError(instance_id) from exc
        except InstanceMigrationError as exc:
            raise InstanceMigrationServiceError(
                instance_id,
                exc.reason,
                blockers=exc.blockers,
            ) from exc

        if not dry_run and not result.get("applied"):
            raise InstanceMigrationServiceError(
                instance_id,
                "migration blocked",
                blockers=list(result.get("blockers") or []),
                result=result,
            )
        return result

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