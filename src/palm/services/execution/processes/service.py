"""Process execution service — process-scoped runs."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import (
    PreparePlansCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.services.base import BaseService
from palm.core.orchestration import Job
from palm.services.execution.processes.grammar import ProcessCommandKind, parse_process_command

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


class ProcessExecutionService(BaseService):
    """Process-scoped execution — composes plan prepare/submit CQRS."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver

    def dispatch(
        self,
        path: list[str] | tuple[str, ...],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a REPL-style command path and return the domain result."""
        params = params or {}
        parsed = parse_process_command(path)
        body = dict(params.get("body") or {})

        if parsed.kind == ProcessCommandKind.PREPARE:
            assert parsed.process_id is not None
            return self.prepare(
                parsed.process_id,
                by_id=bool(params.get("by_id", False)),
                job_id=_optional_str(params.get("job_id")),
                body=body,
                runtime_name=params.get("runtime_name"),
            )

        if parsed.kind == ProcessCommandKind.SUBMIT:
            plan_ids = params.get("plan_ids")
            if plan_ids is None:
                raw = params.get("body") or {}
                if isinstance(raw, dict):
                    plan_ids = raw.get("plan_ids")
            if not plan_ids:
                raise ValueError("plan_ids is required for process submit")
            return self.submit(
                [str(plan_id) for plan_id in plan_ids],
                runtime_name=params.get("runtime_name"),
            )

        if parsed.kind == ProcessCommandKind.RUN:
            assert parsed.process_id is not None
            return self.run(
                parsed.process_id,
                by_id=bool(params.get("by_id", False)),
                job_id=_optional_str(params.get("job_id")),
                body=body,
                runtime_name=params.get("runtime_name"),
            )

        raise RuntimeError(f"unhandled process command: {parsed}")

    def prepare(
        self,
        process_id: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        body: dict[str, Any] | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Stage execution plans for deferred submission."""
        request_body = _prepare_body(
            process_id,
            by_id=by_id,
            job_id=job_id,
            body=body,
        )
        result = self.dispatch_command(
            PreparePlansCommand(body=request_body, runtime_name=runtime_name)
        )
        if not isinstance(result, dict):
            raise TypeError("prepare must return a dict")
        return result

    def submit(
        self,
        plan_ids: list[str],
        *,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Consume staged plan ids and submit orchestration jobs."""
        result = self.dispatch_command(
            SubmitPlansCommand(plan_ids=plan_ids, runtime_name=runtime_name)
        )
        if not isinstance(result, dict):
            raise TypeError("submit must return a dict")
        self.wait_until_idle()
        runtime = self.resolve_runtime(runtime_name)
        for item in result.get("jobs", []):
            if not isinstance(item, dict):
                continue
            job = runtime.get_job(str(item["job_id"]))
            item["status"] = job.status.value
        return result

    def run(
        self,
        process_id: str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        body: dict[str, Any] | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Submit a process in one call (convenience — no plan staging)."""
        request_body = _prepare_body(
            process_id,
            by_id=by_id,
            job_id=job_id,
            body=body,
        )
        result = self.dispatch_command(
            SubmitProcessCommand(
                process=request_body,
                runtime_name=runtime_name,
                by_id=by_id,
                job_id=job_id,
            )
        )
        self.wait_until_idle()
        return _jobs_payload(result)

    def resolve_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        if self._runtime_resolver is not None:
            return self._runtime_resolver(runtime_name)
        if self._runtime is not None:
            return self._runtime
        raise RuntimeError("ProcessExecutionService requires a runtime or runtime_resolver")

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        return self.resolve_runtime().wait_until_idle(timeout=timeout)

    def dispatch_command(self, command: Any) -> Any:
        """Dispatch a CQRS command through the validated bus."""
        return super().dispatch(command)


def _prepare_body(
    process_id: str,
    *,
    by_id: bool = False,
    job_id: str | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(body or {})
    if "process" not in merged and "process_name" not in merged:
        merged["process_name"] = process_id
        if by_id:
            merged["by_id"] = True
    if job_id is not None and "job_id" not in merged:
        merged["job_id"] = job_id
    return merged


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


def _jobs_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        jobs = [_job_row(item) for item in result]
    else:
        jobs = [_job_row(result)]
    return {"jobs": jobs}


def _job_row(job: Any) -> dict[str, Any]:
    if isinstance(job, Job):
        return {
            "job_id": job.id,
            "status": job.status.value,
            "metadata": dict(job.metadata),
        }
    if isinstance(job, dict):
        return job
    raise TypeError(f"unexpected job result type: {type(job)!r}")


__all__ = ["ProcessExecutionService"]