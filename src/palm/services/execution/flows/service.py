"""Flow execution service — interactive session REPL."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.query import GetFlowQuery, ListFlowsQuery
from palm.common.exceptions import InstanceNotFoundError
from palm.common.job_context import instance_id_for_job
from palm.common.operator.flows_session_input import flatten_session_read_model
from palm.common.patterns._registry import enrich_session_view
from palm.common.services.base import BaseService
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.definitions.flows import flow_catalog_row
from palm.services.execution.flows.grammar import FlowCommandKind, parse_flow_command
from palm.services.execution.flows.schemas import SessionContext, build_session_context
from palm.services.execution.flows.session import FlowSession

if TYPE_CHECKING:
    from palm.services.inspect.service import InspectService
    from palm.services.session.bound_surface import BoundSurface
    from palm.services.session.service import SessionService
    from palm.system.runtime.base import BaseRuntime


class FlowExecutionService(BaseService):
    """Run flows and drive sessions — composes CQRS and interactive runtime helpers."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        inspect: InspectService | None = None,
        session: SessionService | None = None,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
        system: InspectService | None = None,
        admission_source: Callable[[], Any] | Any | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        door = inspect if inspect is not None else system
        if door is None:
            raise TypeError("FlowExecutionService requires inspect= (or system= alias)")
        self._inspect = door
        self._session = session
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver
        # 0.63.30–0.63.32 — published admission for product
        # start + continue (same shape as AssistService; no product base class).
        self._admission_source = admission_source

    @property
    def sessions(self) -> SessionService | None:
        """Product session door when host-wired (0.58.12)."""
        return self._session

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
                # Path segment may be definition id (flow-…) or human name
                # (todo-builder). Prefer by_id only for id-shaped refs so Assist
                # and Portal keep working with catalog names (0.58.7).
                if str(parsed.flow_id).startswith("flow-"):
                    body.setdefault("by_id", True)
            session = self.run_wizard(body)
            ctx = session.context()
            # Product FlowSession still keys by instance (SI-001 internal).
            # Envelope law 0.58.9: session_id = system subject; instance_id = continue.
            instance_id = session.session_id
            system_sid = _system_session_from_instance_meta(
                self.get_instance_metadata(instance_id)
            )
            if not system_sid and self._session is not None:
                system_sid = self._session.system_session_from_instance(instance_id)
            elif not system_sid:
                # Plane reverse index is source of truth when instance meta lags.
                try:
                    plane = getattr(self.resolve_runtime(), "session_plane", None)
                    if plane is not None:
                        owner = plane.session_for_instance(instance_id)
                        if owner is not None:
                            system_sid = str(owner.session_id)
                except Exception:
                    system_sid = None
            payload: dict[str, Any] = {
                "instance_id": instance_id,
                "flow_id": session.flow_id,
                "job_id": ctx.job_id,
                "status": ctx.status,
            }
            if system_sid:
                payload["session_id"] = system_sid
            return payload

        if parsed.kind == FlowCommandKind.SESSION:
            assert parsed.flow_id is not None
            assert parsed.session_id is not None
            instance_id = self._resolve_instance_id(parsed.session_id)
            self._gate_bound_session_owns(instance_id, params)
            return self.session(parsed.flow_id, instance_id).context(sync_gate=True)

        if parsed.kind == FlowCommandKind.SESSION_VERB:
            assert parsed.flow_id is not None
            assert parsed.session_id is not None
            assert parsed.verb is not None
            instance_id = self._resolve_instance_id(parsed.session_id)
            self._gate_bound_session_owns(instance_id, params)
            handle = self.session(parsed.flow_id, instance_id)
            if parsed.verb == "input":
                from palm.common.operator.flows_session_input import apply_flows_session_input

                return apply_flows_session_input(
                    get_context=handle.context,
                    provide_input=lambda value: handle.input(value, params=params),
                    params=params,
                )
            if parsed.verb == "backtrack":
                return handle.backtrack(params.get("to_step"))
            if parsed.verb == "resume":
                handle.resume()
                return handle.context()
            if parsed.verb == "cancel":
                return handle.cancel()

        raise RuntimeError(f"unhandled flow command: {parsed}")

    def session(self, flow_id: str | None, session_id: str) -> FlowSession:
        """Return a handle bound to a durable product instance.

        ``session_id`` may be a system subject (``sess-…``); then the primary
        continue instance is resolved via SessionService / plane (0.58.9+).
        """
        return FlowSession(
            self,
            flow_id=flow_id,
            session_id=self._resolve_instance_id(session_id),
        )

    def _resolve_instance_id(self, session_or_instance: str) -> str:
        """Map system session → continue instance; pass instance ids through."""
        if self._session is not None:
            return self._session.resolve_instance_id(session_or_instance)
        text = str(session_or_instance or "").strip()
        if not text.startswith("sess-"):
            return text
        try:
            plane = getattr(self.resolve_runtime(), "session_plane", None)
            if plane is None:
                return text
            inst = plane.resolve_continue_instance(text)
            return str(inst) if inst else text
        except Exception:
            return text

    def _gate_bound_session_owns(
        self, instance_id: str, params: dict[str, Any] | None
    ) -> None:
        """Continue attribution: SI-015 owner + 0.58.15 strict (product door).

        Prefers product SessionService. Plane fallback uses
        ``require_continue_attribution`` (strict) when the plane is ready.
        """
        if self._session is not None:
            self._session.gate_bound_session_owns(instance_id, params)
            return
        params = params if params is not None else {}
        from palm.system.subsystems.planes.session import looks_like_system_session_id

        plane = getattr(self.resolve_runtime(), "session_plane", None)
        if plane is None:
            return
        raw = params.get("session_id")
        sid = str(raw).strip() if looks_like_system_session_id(raw) else None
        if hasattr(plane, "require_continue_attribution"):
            bound = plane.require_continue_attribution(
                str(instance_id).strip(), sid, strict=True
            )
            if bound and not looks_like_system_session_id(params.get("session_id")):
                params["session_id"] = bound
            return
        if sid is not None:
            plane.require_owned_instance(sid, str(instance_id).strip())

    def submit_flow_body(self, body: dict[str, Any]) -> Any:
        """Submit any flow from a REST-shaped body and wait until idle (work drain, triggers).

        **0.63.32:** product start edge fails closed via ``admission_gate()``
        (published admission — same law as continue; port remains a second admission check).
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self.admission_gate())
        job = self.dispatch_command(flow_command_from_body(self._with_system_session(body)))
        self.wait_until_idle()
        return job

    def run_wizard(self, body: dict[str, Any]) -> FlowSession:
        """Submit a wizard flow and return a session on the new instance.

        **0.63.32:** gates via ``submit_flow_body`` (product start).
        """
        job = self.submit_flow_body(body)
        session_id = instance_id_for_job(job)
        flow_id = _flow_id_from_body(body)
        return self.session(flow_id, session_id)

    def _with_system_session(self, body: dict[str, Any]) -> dict[str, Any]:
        """Ensure job metadata carries a system session id (0.58.6 / 0.58.12).

        **Law:** edge and job metadata use one name — ``session_id`` — for the
        system subject (typically ``sess-…``). ``instance_id`` is the continue
        handle. Instance-shaped body ``session_id`` is **not** promoted (product
        must adapt; SI-001). Prefer SessionService.enrich_submit_body.
        """
        if self._session is not None:
            return self._session.enrich_submit_body(body, surface="execution")
        out = dict(body or {})
        meta = dict(out.get("metadata") or {})
        candidates = (
            out.get("session_id")
            if _looks_like_system_session_id(out.get("session_id"))
            else None,
            meta.get("session_id")
            if _looks_like_system_session_id(meta.get("session_id"))
            else None,
        )
        sid = None
        for raw in candidates:
            if raw is not None and str(raw).strip():
                sid = str(raw).strip()
                break
        if sid is None:
            try:
                runtime = self.resolve_runtime()
                plane = getattr(runtime, "session_plane", None)
                if plane is not None:
                    bind = plane.bind(
                        surface="execution",
                        metadata={"via": "flow_submit"},
                    )
                    sid = str(bind.session_id)
            except Exception:
                sid = None
        if sid:
            meta["session_id"] = sid
            out["metadata"] = meta
        return out

    def run_flow(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> FlowSession:
        """Submit a flow and return a session on the new instance.

        **0.63.32:** product start edge fails closed via ``admission_gate()``.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self.admission_gate())
        job = self.dispatch_command(
            SubmitFlowCommand(
                flow=flow,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata=metadata or {},
            )
        )
        self.wait_until_idle()
        session_id = instance_id_for_job(job)
        flow_id = str(flow) if isinstance(flow, str) else None
        return self.session(flow_id, session_id)

    def spawn_sibling(
        self,
        session_id: str,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
    ) -> BoundSurface:
        """Start named work as a same-session sibling (0.69.3).

        Execution start with no ``session_id`` on the job, then session-side
        attach. Does not open ``WaitInterest`` on parked jobs. Nested park
        (``until_input``) is leftover, not this door. Kit start() later.
        """
        from palm.system.structure.errors import require_business_admission

        if self._session is None:
            raise RuntimeError("FlowExecutionService.spawn_sibling requires session=")
        require_business_admission(self.admission_gate())
        job = self.dispatch_command(
            SubmitFlowCommand(
                flow=flow,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata={},
            )
        )
        self.wait_until_idle()
        return self._session.attach_after_start(session_id, instance_id_for_job(job))

    def inspect_session(self, session_id: str) -> dict[str, Any]:
        """Delegate to system inspect for session status views."""
        return self._inspect.inspect_instance(self._resolve_instance_id(session_id))

    def get_instance_metadata(self, session_id: str) -> dict[str, Any]:
        """Return durable metadata for an instance (or system session → resolve)."""
        repository = self._instance_repository()
        if repository is None:
            return {}
        iid = self._resolve_instance_id(session_id)
        try:
            return dict(repository.get(iid).metadata or {})
        except InstanceNotFoundError:
            return {}

    def sync_mutation_gate(self, session_id: str, ctx: SessionContext) -> dict[str, Any] | None:
        """Issue and persist an input token when the session is waiting for input."""
        from palm.common.operator.mutation_gate import issue_on_inspect

        repository = self._instance_repository()
        if repository is None:
            return None
        inspect = flatten_session_read_model(ctx)
        self._sync_operator_mode(repository, session_id, inspect)
        return issue_on_inspect(repository, session_id, inspect)

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
        except Exception:
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

    def admission_gate(self) -> object:
        """Published admission source for product start + continue (0.63.30–32).

        Prefer injected *admission_source*. Fallback digs the runtime shell only
        when packaging omitted the inject — same shape as AssistService.
        """
        if self._admission_source is not None:
            return self._admission_source
        return self.resolve_runtime()

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)

    def dispatch_command(self, command: Any) -> Any:
        """Dispatch a CQRS command through the validated bus."""
        return super().dispatch(command)


def _looks_like_system_session_id(value: Any) -> bool:
    """True when id is system-session shaped (not a bare instance id)."""
    from palm.system.subsystems.planes.session import looks_like_system_session_id

    return looks_like_system_session_id(value)


def _system_session_from_instance_meta(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    raw = metadata.get("session_id")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _submission_extras(body: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    metadata = dict(body["metadata"]) if isinstance(body.get("metadata"), dict) else {}
    return metadata, body.get("state")


def flow_command_from_body(body: dict[str, Any]) -> SubmitFlowCommand:
    """Build :class:`SubmitFlowCommand` from REST/MCP-style submission bodies."""
    metadata, state = _submission_extras(body)
    if "flow" in body and isinstance(body["flow"], dict):
        payload = dict(body["flow"])
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return SubmitFlowCommand(flow=payload, metadata=metadata, state=state)
    if "wizard" in body:
        return SubmitFlowCommand(
            flow={
                "wizard": body["wizard"],
                **({"job_id": body["job_id"]} if body.get("job_id") is not None else {}),
            },
            metadata=metadata,
            state=state,
        )
    if "flow_name" in body:
        return SubmitFlowCommand(
            flow=str(body["flow_name"]),
            by_id=bool(body.get("by_id", False)),
            job_id=_optional_str(body.get("job_id")),
            metadata=metadata,
            state=state,
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