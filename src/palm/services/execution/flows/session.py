"""Flow session handles — session-centric execution API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.child_wait import resume_child_wait_for_instance
from palm.common.cqrs.command import CancelJobCommand
from palm.common.exceptions import InstanceNotFoundError
from palm.common.operator.flows_session_input import flatten_session_read_model
from palm.common.interactive_runtime import (
    provide_interactive_input_for_instance,
    request_interactive_backtrack_for_instance,
    resolve_interactive_job,
)
from palm.core.orchestration import JobStatus
from palm.patterns._registry import enrich_session_view
from palm.services.execution.flows.schemas import SessionContext, build_session_context

if TYPE_CHECKING:
    from palm.services.execution.flows.service import FlowExecutionService


class FlowSession:
    """Stateful handle for one durable flow session."""

    def __init__(
        self,
        flows: FlowExecutionService,
        *,
        flow_id: str | None,
        session_id: str,
    ) -> None:
        self._flows = flows
        self.flow_id = flow_id
        self.session_id = session_id

    def context(self, *, sync_gate: bool = False) -> SessionContext:
        """Pattern-aware session view with command-path hints."""
        view = self._flows.inspect_session(self.session_id)
        ctx = build_session_context(
            flow_id=self.flow_id,
            session_id=self.session_id,
            view=view,
            enricher=enrich_session_view,
        )
        if sync_gate:
            self._flows.sync_mutation_gate(self.session_id, ctx)
        return ctx

    def status(self) -> dict[str, Any]:
        """Return session context as a plain dict."""
        return self.context().to_dict()

    def input(self, value: Any, *, params: dict[str, Any] | None = None) -> SessionContext:
        """Deliver interactive input; returns updated session context."""
        params = params or {}
        from palm.common.operator.mutation_gate import assert_on_write, should_validate_mutation

        if should_validate_mutation(params):
            view = self._flows.inspect_session(self.session_id)
            inspect = flatten_session_read_model(
                build_session_context(
                    flow_id=self.flow_id,
                    session_id=self.session_id,
                    view=view,
                    enricher=enrich_session_view,
                )
            )
            assert_on_write(
                params,
                session_id=self.session_id,
                instance_metadata=self._flows.get_instance_metadata(self.session_id),
                inspect=inspect,
            )
        runtime = self._flows.resolve_runtime()
        try:
            _job, slug = provide_interactive_input_for_instance(
                runtime,
                self.session_id,
                value,
            )
        except InstanceNotFoundError as exc:
            raise exc
        except (TypeError, RuntimeError, ValueError) as exc:
            raise exc

        self._flows.wait_until_idle()
        ctx = self.context(sync_gate=True)
        if slug is not None:
            ctx.detail["slug"] = slug
        return ctx

    def backtrack(self, to_step: str | None = None) -> SessionContext:
        """Backtrack an interactive flow to a prior step."""
        runtime = self._flows.resolve_runtime()
        try:
            _job, target = request_interactive_backtrack_for_instance(
                runtime,
                self.session_id,
                to_step,
            )
        except InstanceNotFoundError as exc:
            raise exc
        except (TypeError, RuntimeError, ValueError) as exc:
            raise exc

        self._flows.wait_until_idle()
        ctx = self.context()
        ctx.detail["to_step"] = target
        return ctx

    def resume(self) -> FlowSession:
        """Re-drive a waiting interactive flow (for example auto-run a resource step)."""
        runtime = self._flows.resolve_runtime()
        try:
            job = resolve_interactive_job(runtime, self.session_id)
            if job.status != JobStatus.WAITING_FOR_INPUT:
                raise RuntimeError(
                    f"Session {self.session_id!r} is not waiting for input "
                    f"(status={job.status.value})"
                )
            runtime.orchestration.resume_job(job.id)
        except InstanceNotFoundError as exc:
            raise exc
        except RuntimeError as exc:
            raise exc

        self._flows.wait_until_idle()
        return self

    def resume_child_wait(self) -> SessionContext:
        """Re-check nested child flow and advance parent when ready."""
        runtime = self._flows.resolve_runtime()
        try:
            resume_child_wait_for_instance(runtime, self.session_id)
        except InstanceNotFoundError as exc:
            raise exc
        except RuntimeError as exc:
            raise exc

        self._flows.wait_until_idle()
        return self.context()

    def cancel(self) -> dict[str, Any]:
        """Cancel the orchestration job backing this session."""
        view = self._flows.inspect_session(self.session_id)
        job_id = str(view.get("job_id") or self.session_id)
        result = self._flows.dispatch_command(CancelJobCommand(job_id=job_id))
        self._flows.wait_until_idle()
        return result if isinstance(result, dict) else {"result": result}


class ReplSession:
    """Stateful CLI handle — tracks the active session across REPL commands."""

    def __init__(self, flows: FlowExecutionService) -> None:
        self._flows = flows
        self._active_flow_id: str | None = None
        self._active_session_id: str | None = None

    def activate(self, session_id: str, *, flow_id: str | None = None) -> FlowSession:
        """Focus the REPL on a durable session."""
        self._active_session_id = session_id
        self._active_flow_id = flow_id
        return self._flows.session(flow_id, session_id)

    def run_wizard(self, body: dict[str, Any]) -> FlowSession:
        """Start a wizard flow and make it the active session."""
        session = self._flows.run_wizard(body)
        self._active_flow_id = session.flow_id
        self._active_session_id = session.session_id
        return session

    def run_flow(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FlowSession:
        """Start a flow and make it the active session."""
        session = self._flows.run_flow(
            flow,
            by_id=by_id,
            job_id=job_id,
            metadata=metadata,
        )
        self._active_flow_id = session.flow_id
        self._active_session_id = session.session_id
        return session

    @property
    def active(self) -> FlowSession | None:
        if self._active_session_id is None:
            return None
        return self._flows.session(self._active_flow_id, self._active_session_id)

    @property
    def active_session_id(self) -> str | None:
        return self._active_session_id

    @property
    def active_flow_id(self) -> str | None:
        return self._active_flow_id

    def clear(self) -> None:
        self._active_flow_id = None
        self._active_session_id = None


__all__ = ["FlowSession", "ReplSession"]