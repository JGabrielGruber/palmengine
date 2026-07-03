"""Flow execution service — interactive session REPL."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.query import GetFlowQuery, ListFlowsQuery
from palm.common.exceptions import InstanceNotFoundError
from palm.common.job_context import instance_id_for_job
from palm.common.operator.flows_session_input import flatten_session_read_model
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.definitions.flows import flow_catalog_row
from palm.services.execution.flows.grammar import FlowCommandKind, parse_flow_command
from palm.services.execution.flows.schemas import SessionContext, build_session_context
from palm.patterns._registry import enrich_session_view
from palm.services.execution.flows.session import FlowSession

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.services.system.service import SystemService


class FlowExecutionService(BaseService):
    """Run flows and drive sessions — composes CQRS and interactive runtime helpers."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        system: SystemService,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._system = system
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver

    def dispatch(
        self,
        path: list[str] | tuple[str, ...],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a REPL-style command path and return the domain result."""
        params = params or {}
        parsed = parse_flow_command(path)

        if parsed.kind == FlowCommandKind.LIST:
            flows = self.ask(ListFlowsQuery())
            return [flow_catalog_row(flow) for flow in flows]

        if parsed.kind == FlowCommandKind.DESCRIBE:
            assert parsed.flow_id is not None
            flow = self.ask(GetFlowQuery(flow_id=parsed.flow_id))
            if flow is None:
                raise DefinitionNotFoundServiceError("flow", parsed.flow_id)
            return flow_catalog_row(flow)

        if parsed.kind == FlowCommandKind.CREATE:
            assert parsed.flow_id is not None
            body = dict(params.get("body") or params)
            if "flow" not in body and "wizard" not in body and "flow_name" not in body:
                body["flow_name"] = parsed.flow_id
            session = self.run_wizard(body)
            ctx = session.context()
            return {
                "session_id": session.session_id,
                "flow_id": session.flow_id,
                "job_id": ctx.job_id,
                "status": ctx.status,
            }

        if parsed.kind == FlowCommandKind.SESSION:
            assert parsed.flow_id is not None
            assert parsed.session_id is not None
            return self.session(parsed.flow_id, parsed.session_id).context(sync_gate=True)

        if parsed.kind == FlowCommandKind.SESSION_VERB:
            assert parsed.flow_id is not None
            assert parsed.session_id is not None
            assert parsed.verb is not None
            handle = self.session(parsed.flow_id, parsed.session_id)
            if parsed.verb == "input":
                from palm.common.operator.flows_session_input import apply_flows_session_input

                return apply_flows_session_input(
                    get_context=handle.context,
                    provide_input=lambda value: handle.input(value, params=params),
                    params=params,
                    get_instance_metadata=self.get_instance_metadata,
                )
            if parsed.verb == "backtrack":
                return handle.backtrack(params.get("to_step"))
            if parsed.verb == "resume":
                handle.resume()
                return handle.context()
            if parsed.verb == "resume-child-wait":
                return handle.resume_child_wait()
            if parsed.verb == "cancel":
                return handle.cancel()

        raise RuntimeError(f"unhandled flow command: {parsed}")

    def session(self, flow_id: str | None, session_id: str) -> FlowSession:
        """Return a handle bound to a durable session."""
        return FlowSession(self, flow_id=flow_id, session_id=session_id)

    def run_wizard(self, body: dict[str, Any]) -> FlowSession:
        """Submit a wizard flow and return a session on the new instance."""
        job = self.dispatch_command(flow_command_from_body(body))
        self.wait_until_idle()
        session_id = instance_id_for_job(job)
        flow_id = _flow_id_from_body(body)
        return self.session(flow_id, session_id)

    def run_flow(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FlowSession:
        """Submit a flow and return a session on the new instance."""
        job = self.dispatch_command(
            SubmitFlowCommand(
                flow=flow,
                by_id=by_id,
                job_id=job_id,
                metadata=metadata or {},
            )
        )
        self.wait_until_idle()
        session_id = instance_id_for_job(job)
        flow_id = str(flow) if isinstance(flow, str) else None
        return self.session(flow_id, session_id)

    def inspect_session(self, session_id: str) -> dict[str, Any]:
        """Delegate to system inspect for session status views."""
        return self._system.inspect_instance(session_id)

    def get_instance_metadata(self, session_id: str) -> dict[str, Any]:
        """Return durable metadata for ``session_id`` when persistence is configured."""
        repository = self._instance_repository()
        if repository is None:
            return {}
        try:
            return dict(repository.get(session_id).metadata or {})
        except InstanceNotFoundError:
            return {}

    def sync_mutation_gate(self, session_id: str, ctx: SessionContext) -> dict[str, Any] | None:
        """Issue and persist an input token when the session is waiting for input."""
        from palm.common.operator.mutation_gate import refresh_mutation_gate

        repository = self._instance_repository()
        if repository is None:
            return None
        inspect = flatten_session_read_model(ctx)
        self._sync_operator_mode(repository, session_id, inspect)
        return refresh_mutation_gate(repository, session_id, inspect)

    def _sync_operator_mode(
        self,
        repository: Any,
        session_id: str,
        inspect: dict[str, Any],
    ) -> None:
        step = inspect.get("step") or inspect.get("current_step_slug")
        instance = repository.get(session_id)
        meta = dict(instance.metadata or {})
        if step == "catalog":
            meta["operator_mode"] = "inspect"
        else:
            meta.pop("operator_mode", None)
        instance.metadata = meta
        repository.save(instance)

    def _instance_repository(self) -> Any | None:
        try:
            return self.resolve_runtime().instances
        except RuntimeError:
            return None

    def session_context(
        self,
        *,
        flow_id: str | None,
        session_id: str,
    ) -> SessionContext:
        """Build a :class:`SessionContext` for ``session_id``."""
        view = self.inspect_session(session_id)
        return build_session_context(
            flow_id=flow_id,
            session_id=session_id,
            view=view,
            enricher=enrich_session_view,
        )

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is not None:
            return self._runtime
        raise RuntimeError("FlowExecutionService requires a runtime or runtime_resolver")

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)

    def dispatch_command(self, command: Any) -> Any:
        """Dispatch a CQRS command through the validated bus."""
        return super().dispatch(command)


def flow_command_from_body(body: dict[str, Any]) -> SubmitFlowCommand:
    """Build :class:`SubmitFlowCommand` from REST/MCP-style submission bodies."""
    if "flow" in body and isinstance(body["flow"], dict):
        payload = dict(body["flow"])
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return SubmitFlowCommand(flow=payload)
    if "wizard" in body:
        return SubmitFlowCommand(
            flow={
                "wizard": body["wizard"],
                **({"job_id": body["job_id"]} if body.get("job_id") is not None else {}),
            }
        )
    if "flow_name" in body:
        return SubmitFlowCommand(
            flow=str(body["flow_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
        )
    raise ValueError("expected 'flow', 'wizard', or 'flow_name' in request body")


def _flow_id_from_body(body: dict[str, Any]) -> str | None:
    if "flow_name" in body:
        return str(body["flow_name"])
    wizard = body.get("wizard")
    if isinstance(wizard, dict):
        name = wizard.get("name")
        return str(name) if name is not None else None
    flow = body.get("flow")
    if isinstance(flow, dict):
        for key in ("name", "flow", "flow_name"):
            value = flow.get(key)
            if value is not None:
                return str(value)
    return None


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["FlowExecutionService", "flow_command_from_body"]