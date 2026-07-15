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
    ListResourceInvocationsQuery,
)
from palm.core.registry import pattern_registry
from palm.patterns.wizard.bindings.cqrs.queries import GetWizardStatusQuery

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition
    from palm.runtimes.server.context import ServerContext


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
        return self._ctx.ask(
            GetInstanceSnapshotQuery(instance_id=instance_id, snapshot_id=snapshot_id)
        )

    def get_resource_invocations(
        self,
        *,
        instance_id: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            return self._ctx.ask(
                GetResourceInvocationsQuery(instance_id=instance_id, job_id=job_id),
            )
        except TypeError:
            return None

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

    def list_assist_scenarios(self) -> list[dict[str, Any]]:
        rows = self._ctx.assist.dispatch(["assist", "scenarios"])
        return list(rows) if isinstance(rows, list) else []

    def describe_assist_scenario(self, scenario_id: str) -> dict[str, Any]:
        return self._ctx.assist.dispatch(["assist", "scenarios", scenario_id])

    def start_assist_scenario(
        self,
        scenario_id: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._ctx.assist.start_scenario(scenario_id, body or {}, view_format="assistant")

    def get_assist_session(self, session_id: str) -> dict[str, Any]:
        return (
            self._ctx.assist.session(session_id)
            .context(view_format="assistant")
            .to_dict(view_format="assistant")
        )

    def provide_assist_input(self, session_id: str, value: Any) -> dict[str, Any]:
        return (
            self._ctx.assist.session(session_id)
            .input(value, view_format="assistant")
            .to_dict(view_format="assistant")
        )

    def backtrack_assist_session(
        self,
        session_id: str,
        to_step: str | None = None,
    ) -> dict[str, Any]:
        return (
            self._ctx.assist.session(session_id)
            .backtrack(to_step, view_format="assistant")
            .to_dict(view_format="assistant")
        )

    def cancel_assist_session(self, session_id: str) -> dict[str, Any]:
        return self._ctx.assist.session(session_id).cancel()

    def handoff_assist_session(self, session_id: str) -> dict[str, Any]:
        return self._ctx.assist.handoff(session_id)

    def get_wizard(self, instance_id: str) -> dict[str, Any] | None:
        """Rich wizard view keyed by durable instance id."""
        result = self._ctx.ask(GetWizardStatusQuery(instance_id=instance_id))
        if result is None:
            return None
        if hasattr(result, "to_dict"):
            return result.to_dict()
        if isinstance(result, dict):
            return result
        return None

    def flow_pattern_by_name(self) -> dict[str, str]:
        """Map flow name → pattern for catalog badges."""
        return {flow.name: flow.pattern for flow in self.list_flows()}

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

    def list_resource_invocation_rows(self, *, limit: int = 50) -> list[dict[str, Any]]:
        try:
            rows = self._ctx.ask(ListResourceInvocationsQuery(limit=limit))
        except TypeError:
            return []
        if isinstance(rows, list):
            if rows and hasattr(rows[0], "to_dict"):
                return [row.to_dict() for row in rows]
            return [row for row in rows if isinstance(row, dict)]
        return []

    def invoke_resource(
        self,
        resource_ref: str,
        *,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        state: Any = None,
        resource_id: str | None = None,
    ) -> Any:
        """Invoke a resource definition on the hosting runtime."""
        engine = self._ctx.runtime.resource
        if not engine.is_initialized:
            engine.initialize()
        return engine.invoke(
            resource_ref,
            action=action,
            params=params,
            state=state,
            resource_id=resource_id,
        )

    def describe_resource(self, resource_id: str) -> dict[str, Any] | None:
        from palm.common.exceptions import DefinitionNotFoundError
        from palm.common.resource.catalog import ResourceCatalog

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
