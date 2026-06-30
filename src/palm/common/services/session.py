"""Instance and REPL session handles — instance-centric execution API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.child_wait import resume_child_wait_for_instance
from palm.common.cqrs.command import CancelJobCommand
from palm.common.exceptions import InstanceNotFoundError
from palm.common.interactive_runtime import (
    provide_interactive_input_for_instance,
    request_interactive_backtrack_for_instance,
    resolve_interactive_job,
)
from palm.core.orchestration import JobStatus

if TYPE_CHECKING:
    from palm.common.services.execution import ExecutionService


class InstanceSession:
    """Stateful handle for one durable instance — primary execution metaphor."""

    def __init__(self, execution: ExecutionService, instance_id: str) -> None:
        self._execution = execution
        self.instance_id = instance_id

    def status(self) -> dict[str, Any]:
        """Pattern-aware instance view after inspect."""
        return self._execution.inspect_instance(self.instance_id)

    def input(self, value: Any) -> dict[str, Any]:
        """Deliver interactive input; returns updated instance view."""
        runtime = self._execution.resolve_runtime()
        try:
            _job, slug = provide_interactive_input_for_instance(
                runtime,
                self.instance_id,
                value,
            )
        except InstanceNotFoundError as exc:
            raise exc
        except (TypeError, RuntimeError, ValueError) as exc:
            raise exc

        self._execution.wait_until_idle()
        view = self.status()
        if slug is not None:
            view = {**view, "slug": slug}
        return view

    def backtrack(self, to_step: str | None = None) -> dict[str, Any]:
        """Backtrack an interactive flow to a prior step."""
        runtime = self._execution.resolve_runtime()
        try:
            _job, target = request_interactive_backtrack_for_instance(
                runtime,
                self.instance_id,
                to_step,
            )
        except InstanceNotFoundError as exc:
            raise exc
        except (TypeError, RuntimeError, ValueError) as exc:
            raise exc

        self._execution.wait_until_idle()
        view = self.status()
        return {**view, "to_step": target}

    def resume(self) -> InstanceSession:
        """Re-drive a waiting interactive flow (for example auto-run a resource step)."""
        runtime = self._execution.resolve_runtime()
        try:
            job = resolve_interactive_job(runtime, self.instance_id)
            if job.status != JobStatus.WAITING_FOR_INPUT:
                raise RuntimeError(
                    f"Instance {self.instance_id!r} is not waiting for input "
                    f"(status={job.status.value})"
                )
            runtime.orchestration.resume_job(job.id)
        except InstanceNotFoundError as exc:
            raise exc
        except RuntimeError as exc:
            raise exc

        self._execution.wait_until_idle()
        return self

    def resume_child_wait(self) -> dict[str, Any]:
        """Re-check nested child flow and advance parent when ready."""
        runtime = self._execution.resolve_runtime()
        try:
            resume_child_wait_for_instance(runtime, self.instance_id)
        except InstanceNotFoundError as exc:
            raise exc
        except RuntimeError as exc:
            raise exc

        self._execution.wait_until_idle()
        return self.status()

    def cancel(self) -> dict[str, Any]:
        """Cancel the orchestration job backing this instance."""
        view = self.status()
        job_id = str(view.get("job_id") or self.instance_id)
        result = self._execution.dispatch(CancelJobCommand(job_id=job_id))
        self._execution.wait_until_idle()
        return result if isinstance(result, dict) else {"result": result}


class ReplSession:
    """Stateful CLI handle — tracks the active instance across REPL commands."""

    def __init__(self, execution: ExecutionService) -> None:
        self._execution = execution
        self._active_id: str | None = None

    def activate(self, instance_id: str) -> InstanceSession:
        """Focus the REPL on a durable instance."""
        self._active_id = instance_id
        return self._execution.on(instance_id)

    def run_wizard(self, body: dict[str, Any]) -> InstanceSession:
        """Start a wizard flow and make it the active instance."""
        session = self._execution.run_wizard(body)
        self._active_id = session.instance_id
        return session

    def run_flow(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InstanceSession:
        """Start a flow and make it the active instance."""
        session = self._execution.run_flow(
            flow,
            by_id=by_id,
            job_id=job_id,
            metadata=metadata,
        )
        self._active_id = session.instance_id
        return session

    @property
    def active(self) -> InstanceSession | None:
        if self._active_id is None:
            return None
        return self._execution.on(self._active_id)

    @property
    def active_instance_id(self) -> str | None:
        return self._active_id

    def clear(self) -> None:
        self._active_id = None


__all__ = ["InstanceSession", "ReplSession"]
