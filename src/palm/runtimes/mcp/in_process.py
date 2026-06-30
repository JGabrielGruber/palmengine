"""In-process MCP backend — services and CQRS without HTTP round-trips."""

from __future__ import annotations

import atexit
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import (
    PreparePlansCommand,
    ProvideInputCommand,
    SubmitPlansCommand,
)
from palm.common.cqrs.query import (
    GetInstanceSnapshotQuery,
    GetJobStatusQuery,
    ListInstanceSnapshotsQuery,
)
from palm.common.exceptions import InstanceNotFoundError, PlanNotFoundError
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.common.services.execution import flow_command_from_body
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.rest_client import PalmRestError
from palm.states import BlackboardState

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext
    from palm.runtimes.server.runtime import ServerRuntime


_runtime_holder: ServerRuntime | None = None


def create_in_process_backend(
    config: PalmMcpConfig | None = None,
    *,
    ctx: ServerContext | None = None,
) -> PalmInProcessBackend:
    """Bootstrap or reuse a :class:`ServerContext` for in-process MCP tools."""
    resolved_ctx = ctx if ctx is not None else _bootstrap_server_context()
    return PalmInProcessBackend(resolved_ctx, config=config or PalmMcpConfig.from_env())


def _bootstrap_server_context() -> ServerContext:
    global _runtime_holder
    from palm.runtimes.server import ServerRuntime
    from palm.runtimes.server.factory import build_server_context

    if _runtime_holder is not None and _runtime_holder.is_started:
        return build_server_context(_runtime_holder)

    runtime = ServerRuntime(host="127.0.0.1", port=0)
    runtime.start(http=False)
    _runtime_holder = runtime
    atexit.register(shutdown_in_process_runtime)
    return build_server_context(runtime)


def shutdown_in_process_runtime() -> None:
    """Stop the lazily started in-process server runtime."""
    global _runtime_holder
    runtime = _runtime_holder
    _runtime_holder = None
    if runtime is not None and runtime.is_started:
        runtime.stop()


class PalmInProcessBackend:
    """Duck-typed REST client surface backed by :class:`InternalService` and CQRS."""

    def __init__(
        self,
        ctx: ServerContext,
        *,
        config: PalmMcpConfig | None = None,
    ) -> None:
        self._ctx = ctx
        self._config = config or PalmMcpConfig.from_env()

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def context(self) -> ServerContext:
        return self._ctx

    def get_health(self) -> dict[str, Any]:
        runtime = self._ctx.runtime
        return {
            "status": "ok",
            "runtime": runtime.runtime_name,
            "version": runtime.version,
            "auth_enforce": runtime.auth_enforce,
            "mode": "in_process",
        }

    def list_waiting_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        from palm.common.operator.waiting_jobs import enrich_job_list_rows
        from palm.runtimes.server.surfaces.rest.pagination import list_envelope
        from palm.runtimes.server.surfaces.rest.validation import PaginationParams

        rows = self._ctx.internal.list_jobs(status="WAITING_FOR_INPUT", limit=None)
        rows = enrich_job_list_rows(self._ctx.runtime, rows)
        params = PaginationParams(limit=limit, offset=0)
        return list_envelope("jobs", rows, params)

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        try:
            return self._ctx.internal.inspect_instance(instance_id)
        except InstanceNotFoundServiceError as exc:
            raise _wizard_not_found(exc.instance_id) from exc

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        try:
            return self._ctx.execution.on(instance_id).input(value)
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(instance_id) from exc
        except TypeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except (ValueError, RuntimeError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def resume_child_wait(self, instance_id: str) -> dict[str, Any]:
        try:
            return self._ctx.execution.on(instance_id).resume_child_wait()
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(instance_id) from exc
        except RuntimeError as exc:
            raise PalmRestError(400, str(exc)) from exc

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        try:
            return build_invoke_tree(self._ctx.runtime, instance_id, base_url=None)
        except InstanceNotFoundError as exc:
            raise _instance_not_found(instance_id) from exc

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        result = self._ctx.internal.inspect_job(job_id)
        if isinstance(result, dict) and not result.get("found", True):
            raise _job_not_found(job_id)
        return result

    def provide_job_input(self, job_id: str, value: Any) -> dict[str, Any]:
        try:
            slug = self._ctx.execute(ProvideInputCommand(job_id=job_id, value=value))
        except JobNotFoundError as exc:
            raise _job_not_found(job_id) from exc
        except (TypeError, RuntimeError) as exc:
            raise PalmRestError(400, str(exc)) from exc

        self._ctx.wait_until_idle()
        job_view = self._ctx.ask(GetJobStatusQuery(job_id=job_id))
        status = (
            job_view.get("status")
            if isinstance(job_view, dict)
            else getattr(job_view, "status", "")
        )
        step = job_view.get("step") if isinstance(job_view, dict) else None
        return {"job_id": job_id, "slug": slug, "status": status, "step": step}

    def resume_wizard_tick(self, instance_id: str) -> dict[str, Any]:
        try:
            self._ctx.execution.on(instance_id).resume()
            return self.get_wizard(instance_id)
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(instance_id) from exc
        except RuntimeError as exc:
            raise PalmRestError(400, str(exc)) from exc

    def backtrack_wizard(self, instance_id: str, *, to_step: str | None = None) -> dict[str, Any]:
        try:
            return self._ctx.execution.on(instance_id).backtrack(to_step)
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(instance_id) from exc
        except TypeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except ValueError as exc:
            raise PalmRestError(400, str(exc)) from exc

    def submit_wizard(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            session = self._ctx.execution.run_wizard(body)
            view = session.status()
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except Exception as exc:
            raise PalmRestError(500, str(exc)) from exc

        return {
            "instance_id": session.instance_id,
            "job_id": view.get("job_id"),
            "status": view.get("status"),
            "metadata": view.get("metadata") or {},
        }

    def submit_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            command = flow_command_from_body(body)
            session = self._ctx.execution.run_flow(
                command.flow,
                by_id=command.by_id,
                job_id=command.job_id,
            )
            view = session.status()
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except Exception as exc:
            raise PalmRestError(500, str(exc)) from exc

        return {
            "job_id": view.get("job_id"),
            "status": view.get("status"),
            "metadata": view.get("metadata") or {},
        }

    def list_flows(self, *, pattern: str | None = None) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.pagination import list_envelope
        from palm.runtimes.server.surfaces.rest.validation import PaginationParams

        rows = self._ctx.definition.list_flows(pattern=pattern)
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("flows", rows, params)

    def get_flow(self, flow_id: str, *, verbose: bool = False) -> dict[str, Any]:
        try:
            return self._ctx.definition.get_flow(flow_id, verbose=verbose)
        except DefinitionNotFoundServiceError as exc:
            raise _flow_not_found(exc.ref) from exc

    def list_processes(self) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.pagination import list_envelope
        from palm.runtimes.server.surfaces.rest.validation import PaginationParams

        rows = self._ctx.definition.list_processes()
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("processes", rows, params)

    def get_process(self, process_id: str) -> dict[str, Any]:
        try:
            return self._ctx.definition.get_process(process_id)
        except DefinitionNotFoundServiceError as exc:
            raise _process_not_found(exc.ref) from exc

    def list_resources(self, *, provider: str | None = None) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.pagination import list_envelope
        from palm.runtimes.server.surfaces.rest.validation import PaginationParams

        rows = self._ctx.definition.list_resources(provider=provider)
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("resources", rows, params)

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        try:
            return self._ctx.definition.get_resource(resource_ref)
        except DefinitionNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "resource_not_found",
                    "message": str(exc),
                    "resource_ref": resource_ref,
                },
            ) from exc

    def get_openapi(self) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.openapi import build_openapi_spec

        return build_openapi_spec(version=self._ctx.runtime.version)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        result = self._ctx.internal.cancel_job(job_id)
        if isinstance(result, dict) and not result.get("found", True):
            raise _job_not_found(job_id)
        return result

    def prepare_plans(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._ctx.execute(PreparePlansCommand(body=body))
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def submit_plans(self, plan_ids: list[str]) -> dict[str, Any]:
        try:
            result = self._ctx.execute(SubmitPlansCommand(plan_ids=plan_ids))
        except PlanNotFoundError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "plan_not_found",
                    "message": f"Plan not found: {exc.plan_id}",
                    "plan_id": exc.plan_id,
                },
            ) from exc
        except Exception as exc:
            raise PalmRestError(500, str(exc)) from exc

        self._ctx.wait_until_idle()
        for item in result.get("jobs", []):
            if not isinstance(item, dict):
                continue
            job = self._ctx.runtime.get_job(str(item["job_id"]))
            item["status"] = job.status.value
        return result

    def get_doctor(self) -> dict[str, Any]:
        return self._ctx.internal.doctor(self._ctx.runtime)

    def validate_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._ctx.definition.validate_flow(body, runtime=self._ctx.runtime)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except Exception as exc:
            raise PalmRestError(
                400,
                {
                    "error": "validation_failed",
                    "message": str(exc),
                    "details": [{"field": "flow", "message": str(exc), "code": "build_failed"}],
                },
            ) from exc

    def list_snapshots(self, instance_id: str) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.pagination import list_envelope
        from palm.runtimes.server.surfaces.rest.serializers import snapshot_summary
        from palm.runtimes.server.surfaces.rest.validation import PaginationParams

        try:
            snapshots = self._ctx.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))
        except InstanceNotFoundError as exc:
            raise _instance_not_found(instance_id) from exc

        rows = [snapshot_summary(index, snap) for index, snap in enumerate(snapshots)]
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("snapshots", rows, params)

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> dict[str, Any]:
        from palm.runtimes.server.surfaces.rest.serializers import snapshot_detail

        try:
            resolved = self._ctx.ask(
                GetInstanceSnapshotQuery(instance_id=instance_id, snapshot_id=snapshot_id)
            )
        except InstanceNotFoundError as exc:
            raise _instance_not_found(instance_id) from exc

        if resolved is None:
            raise PalmRestError(
                404,
                {
                    "error": "snapshot_not_found",
                    "message": f"Snapshot not found: {snapshot_id}",
                    "instance_id": instance_id,
                    "snapshot_id": snapshot_id,
                },
            )

        index, snapshot = resolved
        return snapshot_detail(index, snapshot)

    def invoke_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        resource_ref = str(body.get("resource_ref") or "").strip()
        if not resource_ref:
            raise PalmRestError(400, "resource_ref is required")

        engine = self._ctx.runtime.resource
        if not engine.is_initialized:
            engine.initialize()

        state = _resolve_state(body.get("state"))
        result = engine.invoke(
            resource_ref,
            action=body.get("action"),
            params=body.get("params"),
            state=state,
            resource_id=body.get("resource_id"),
        )
        return _provider_result_body(result)


def _resolve_state(raw: Any) -> BlackboardState | None:
    if raw is None:
        return None
    if isinstance(raw, BlackboardState):
        return raw
    if isinstance(raw, dict):
        return BlackboardState(raw)
    return None


def _provider_result_body(result: Any) -> dict[str, Any]:
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "metadata": dict(result.metadata),
    }


def _wizard_not_found(instance_id: str) -> PalmRestError:
    return PalmRestError(
        404,
        {
            "error": "wizard_not_found",
            "message": f"Wizard not found: {instance_id}",
            "instance_id": instance_id,
        },
    )


def _instance_not_found(instance_id: str) -> PalmRestError:
    return PalmRestError(
        404,
        {
            "error": "instance_not_found",
            "message": f"Instance not found: {instance_id}",
            "instance_id": instance_id,
        },
    )


def _job_not_found(job_id: str) -> PalmRestError:
    return PalmRestError(
        404,
        {
            "error": "job_not_found",
            "message": f"Job not found: {job_id}",
            "job_id": job_id,
        },
    )


def _flow_not_found(flow_id: str) -> PalmRestError:
    return PalmRestError(
        404,
        {
            "error": "flow_not_found",
            "message": f"Flow not found: {flow_id}",
            "flow_id": flow_id,
        },
    )


def _process_not_found(process_id: str) -> PalmRestError:
    return PalmRestError(
        404,
        {
            "error": "process_not_found",
            "message": f"Process not found: {process_id}",
            "process_id": process_id,
        },
    )


__all__ = [
    "PalmInProcessBackend",
    "create_in_process_backend",
    "shutdown_in_process_runtime",
]
