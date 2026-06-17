"""SSR data fetching — read models via the shared CQRS query bus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import (
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    GetResourceInvocationsQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
)
from palm.core.registry import pattern_registry

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition


class ExplorerFetcher:
    """Thin CQRS facade for Palm Explorer pages."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx

    @property
    def version(self) -> str:
        return self._ctx.runtime.version

    def list_flows(self, *, pattern: str | None = None) -> list[FlowDefinition]:
        return self._ctx.ask(ListFlowsQuery(pattern=pattern))

    def get_flow(self, flow_id: str) -> FlowDefinition | None:
        return self._ctx.ask(GetFlowQuery(flow_id=flow_id))

    def list_processes(self) -> list[ProcessDefinition]:
        return self._ctx.ask(ListProcessesQuery())

    def get_process(self, process_id: str) -> ProcessDefinition | None:
        return self._ctx.ask(GetProcessQuery(process_id=process_id))

    def list_jobs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._ctx.ask(ListJobStatusQuery(limit=limit))
        if rows and hasattr(rows[0], "to_dict"):
            return [row.to_dict() for row in rows]
        return list(rows)

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        return self._ctx.ask(GetJobContextQuery(job_id=job_id))

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        return self._ctx.ask(GetJobStatusQuery(job_id=job_id))

    def list_instances(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._ctx.ask(ListInstancesQuery(limit=limit, include_terminal=True))
        if rows and hasattr(rows[0], "to_dict"):
            return [row.to_dict() for row in rows]
        return list(rows)

    def list_snapshots(self, instance_id: str) -> list[Any]:
        return self._ctx.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> Any:
        return self._ctx.ask(GetInstanceSnapshotQuery(instance_id=instance_id, snapshot_id=snapshot_id))

    def get_resource_invocations(
        self,
        *,
        instance_id: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any] | None:
        return self._ctx.ask(GetResourceInvocationsQuery(instance_id=instance_id, job_id=job_id))

    def get_instance(self, instance_id: str) -> dict[str, Any] | None:
        result = self._ctx.ask(GetInstanceStatusQuery(instance_id=instance_id))
        if isinstance(result, dict):
            if not result.get("found", True):
                return None
            return result
        if result is None:
            return None
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return dict(result)

    def list_patterns(self) -> list[dict[str, str]]:
        import palm.patterns  # noqa: F401 — register installed patterns

        items: list[dict[str, str]] = []
        for name in pattern_registry.names():
            cls = pattern_registry.get(name)
            doc = (cls.__doc__ or "").strip().split("\n")[0]
            items.append({"name": name, "class": cls.__name__, "summary": doc})
        return items

    def list_resource_catalog(self) -> list[Any]:
        from palm.common.resource.catalog import ResourceCatalog

        return ResourceCatalog(self._ctx.runtime.repository).entries()

    def describe_resource(self, resource_id: str) -> dict[str, Any] | None:
        from palm.common.resource.catalog import ResourceCatalog
        from palm.common.exceptions import DefinitionNotFoundError

        catalog = ResourceCatalog(self._ctx.runtime.repository)
        try:
            return catalog.describe(resource_id, by_id=True)
        except DefinitionNotFoundError:
            try:
                return catalog.describe(resource_id, by_id=False)
            except DefinitionNotFoundError:
                return None

    def list_schemas(self) -> list[dict[str, Any]]:
        schemas: list[dict[str, Any]] = []
        for flow in self.list_flows():
            if flow.state_schema is not None:
                schemas.append(
                    {
                        "flow_id": flow.definition_id,
                        "flow_name": flow.name,
                        "kind": "inline",
                        "schema": flow.state_schema,
                    }
                )
            elif flow.state_schema_ref is not None:
                schemas.append(
                    {
                        "flow_id": flow.definition_id,
                        "flow_name": flow.name,
                        "kind": "ref",
                        "schema_ref": flow.state_schema_ref,
                    }
                )
        return schemas


SsrFetcher = ExplorerFetcher