"""In-process MCP backend — services and CQRS without HTTP round-trips."""

from __future__ import annotations

import atexit
from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import (
    ProvideInputCommand,
)
from palm.common.cqrs.query import (
    GetInstanceSnapshotQuery,
    GetJobStatusQuery,
    ListInstanceSnapshotsQuery,
)
from palm.common.exceptions import InstanceNotFoundError, MutationRejectedError, PlanNotFoundError
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.operator.waiting_jobs import enrich_job_list_rows
from palm.common.services.errors import DefinitionNotFoundServiceError, InstanceNotFoundServiceError
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.runtimes.mcp.assist.dispatch import dispatch_operator_path
from palm.runtimes.mcp.config import PalmMcpConfig
from palm.runtimes.mcp.flows.views import (
    flatten_session_view,
    resolve_flow_id_from_inspect,
    session_context_dict,
    submission_view,
)
from palm.runtimes.mcp.rest_client import PalmRestError, _process_id_from_body
from palm.runtimes.server.surfaces.rest.openapi import build_openapi_spec
from palm.runtimes.server.surfaces.rest.pagination import list_envelope
from palm.runtimes.server.surfaces.rest.serializers import snapshot_detail, snapshot_summary
from palm.runtimes.server.surfaces.rest.validation import PaginationParams
from palm.services.execution.flows import flow_command_from_body
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

    from palm.app.bootstrap import load_definitions_for_repository
    from palm.app.settings import PalmSettings

    runtime = ServerRuntime(host="127.0.0.1", port=0)
    runtime.start(http=False)
    load_definitions_for_repository(runtime.repository, PalmSettings())
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
    """Duck-typed REST client surface backed by :class:`SystemService` and CQRS."""

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
        rows = self._ctx.system.list_jobs(status="WAITING_FOR_INPUT", limit=None)
        rows = enrich_job_list_rows(self._ctx.runtime, rows)
        params = PaginationParams(limit=limit, offset=0)
        return list_envelope("jobs", rows, params)

    def flows_list(self) -> dict[str, Any]:
        rows = self._ctx.execution.flows.dispatch(["flows"])
        params = PaginationParams(limit=len(rows), offset=0)
        return list_envelope("flows", rows, params)

    def flows_describe(self, flow_id: str) -> dict[str, Any]:
        try:
            row = self._ctx.execution.flows.dispatch(["flows", flow_id])
        except DefinitionNotFoundServiceError as exc:
            raise _flow_not_found(exc.ref) from exc
        return row if isinstance(row, dict) else {"value": row}

    def flows_create_session(self, flow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._ctx.execution.flows.dispatch(
                ["flows", flow_id, "create"],
                {"body": body},
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except Exception as exc:
            raise PalmRestError(500, str(exc)) from exc
        return submission_view(result if isinstance(result, dict) else {"result": result})

    def flows_get_session(
        self,
        flow_id: str | None,
        session_id: str,
    ) -> dict[str, Any]:
        try:
            fid = flow_id or self._resolve_flow_id(session_id)
            ctx = self._ctx.execution.flows.dispatch(["flows", fid, "session", session_id])
        except InstanceNotFoundServiceError as exc:
            raise _wizard_not_found(exc.instance_id) from exc
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(session_id) from exc
        return session_context_dict(ctx)

    def get_instance_metadata(self, session_id: str) -> dict[str, Any]:
        try:
            return self._ctx.execution.flows.get_instance_metadata(session_id)
        except Exception:
            return {}

    def flows_session_input(
        self,
        flow_id: str,
        session_id: str,
        value: Any,
        *,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"value": value}
        if input_token is not None:
            params["input_token"] = input_token
        try:
            ctx = self._ctx.execution.flows.dispatch(
                ["flows", flow_id, "session", session_id, "input"],
                params,
            )
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(session_id) from exc
        except MutationRejectedError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except TypeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except (ValueError, RuntimeError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        return session_context_dict(ctx)

    def flows_session_backtrack(
        self,
        flow_id: str,
        session_id: str,
        *,
        to_step: str | None = None,
    ) -> dict[str, Any]:
        try:
            ctx = self._ctx.execution.flows.dispatch(
                ["flows", flow_id, "session", session_id, "backtrack"],
                {"to_step": to_step},
            )
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(session_id) from exc
        except TypeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except ValueError as exc:
            raise PalmRestError(400, str(exc)) from exc
        return session_context_dict(ctx)

    def flows_session_resume(self, flow_id: str, session_id: str) -> dict[str, Any]:
        try:
            ctx = self._ctx.execution.flows.dispatch(
                ["flows", flow_id, "session", session_id, "resume"],
            )
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(session_id) from exc
        except RuntimeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        return session_context_dict(ctx)

    def flows_session_resume_child_wait(
        self,
        flow_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        try:
            ctx = self._ctx.execution.flows.dispatch(
                ["flows", flow_id, "session", session_id, "resume-child-wait"],
            )
        except InstanceNotFoundError as exc:
            raise _wizard_not_found(session_id) from exc
        except RuntimeError as exc:
            raise PalmRestError(400, str(exc)) from exc
        return session_context_dict(ctx)

    def get_wizard(self, instance_id: str) -> dict[str, Any]:
        return flatten_session_view(self.flows_get_session(None, instance_id))

    def provide_wizard_input(self, instance_id: str, value: Any) -> dict[str, Any]:
        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        return flatten_session_view(self.flows_session_input(flow_id, instance_id, value))

    def resume_child_wait(self, instance_id: str) -> dict[str, Any]:
        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        view = self.flows_session_resume_child_wait(flow_id, instance_id)
        return flatten_session_view(view)

    def get_instance_tree(self, instance_id: str) -> dict[str, Any]:
        try:
            return build_invoke_tree(self._ctx.runtime, instance_id, base_url=None)
        except InstanceNotFoundError as exc:
            raise _instance_not_found(instance_id) from exc

    def get_job_context(self, job_id: str) -> dict[str, Any]:
        result = self._ctx.system.inspect_job(job_id)
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
        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        return flatten_session_view(self.flows_session_resume(flow_id, instance_id))

    def backtrack_wizard(self, instance_id: str, *, to_step: str | None = None) -> dict[str, Any]:
        inspect = self.get_wizard(instance_id)
        flow_id = resolve_flow_id_from_inspect(inspect)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {instance_id!r}")
        view = self.flows_session_backtrack(flow_id, instance_id, to_step=to_step)
        return flatten_session_view(view)

    def submit_wizard(self, body: dict[str, Any]) -> dict[str, Any]:
        flow_id = str(body.get("flow_name") or _flow_id_from_submit_body(body) or "flow")
        return self.flows_create_session(flow_id, body)

    def _resolve_flow_id(self, session_id: str) -> str:
        try:
            view = self._ctx.system.inspect_instance(session_id)
        except InstanceNotFoundServiceError as exc:
            raise _wizard_not_found(exc.instance_id) from exc
        flow_id = resolve_flow_id_from_inspect(view)
        if not flow_id:
            raise PalmRestError(400, f"could not resolve flow_id for session {session_id!r}")
        return flow_id

    def submit_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            command = flow_command_from_body(body)
            session = self._ctx.execution.flows.run_flow(
                command.flow,
                by_id=command.by_id,
                job_id=command.job_id,
                metadata=command.metadata,
                state=command.state,
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
        rows = self._ctx.definitions.list_flows(pattern=pattern)
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("flows", rows, params)

    def get_flow(
        self,
        flow_id: str,
        *,
        verbose: bool = False,
        revision: int | None = None,
    ) -> dict[str, Any]:
        try:
            return self._ctx.definitions.get_flow(
                flow_id,
                verbose=verbose,
                revision=revision,
            )
        except DefinitionNotFoundServiceError as exc:
            raise _flow_not_found(exc.ref) from exc

    def analyze_flow_impact(
        self,
        flow_id: str,
        *,
        target_revision: int | None = None,
    ) -> dict[str, Any]:
        try:
            return self._ctx.definitions.analyze_impact(
                flow_id,
                target_revision=target_revision,
            )
        except DefinitionNotFoundServiceError as exc:
            raise _flow_not_found(exc.ref) from exc

    def migrate_instance(
        self,
        instance_id: str,
        *,
        target_revision: int,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        from palm.common.services.errors import InstanceMigrationServiceError

        try:
            return self._ctx.definitions.migrate_instance(
                instance_id,
                target_revision=target_revision,
                dry_run=dry_run,
            )
        except InstanceNotFoundServiceError as exc:
            raise _instance_not_found(exc.instance_id) from exc
        except InstanceMigrationServiceError as exc:
            raise PalmRestError(
                400,
                {
                    "error": "migration_failed",
                    "message": exc.reason,
                    "instance_id": instance_id,
                    "blockers": exc.blockers,
                    "result": exc.result,
                },
            ) from exc

    def list_processes(self) -> dict[str, Any]:
        rows = self._ctx.definitions.list_processes()
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("processes", rows, params)

    def get_process(self, process_id: str) -> dict[str, Any]:
        try:
            return self._ctx.definitions.get_process(process_id)
        except DefinitionNotFoundServiceError as exc:
            raise _process_not_found(exc.ref) from exc

    def list_resources(self, *, provider: str | None = None) -> dict[str, Any]:
        rows = self._ctx.definitions.list_resources(provider=provider)
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("resources", rows, params)

    def get_resource(self, resource_ref: str) -> dict[str, Any]:
        try:
            return self._ctx.definitions.get_resource(resource_ref)
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
        return build_openapi_spec(version=self._ctx.runtime.version)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        result = self._ctx.system.cancel_job(job_id)
        if isinstance(result, dict) and not result.get("found", True):
            raise _job_not_found(job_id)
        return result

    def prepare_plans(self, body: dict[str, Any]) -> dict[str, Any]:
        process_id = _process_id_from_body(body)
        try:
            return self._ctx.execution.processes.prepare(process_id, body=body)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def submit_plans(self, plan_ids: list[str]) -> dict[str, Any]:
        try:
            return self._ctx.execution.processes.submit(plan_ids)
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

    def get_doctor(self) -> dict[str, Any]:
        return self._ctx.system.doctor(self._ctx.runtime)

    def assist_dispatch(
        self,
        path: list[str],
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            return dispatch_operator_path(self._ctx, path, params)
        except DefinitionNotFoundServiceError as exc:
            if exc.kind == "flow":
                raise _flow_not_found(exc.ref) from exc
            if exc.kind == "process":
                raise _process_not_found(exc.ref) from exc
            raise PalmRestError(
                404,
                {"error": f"{exc.kind}_not_found", "message": str(exc), "ref": exc.ref},
            ) from exc
        except InstanceNotFoundServiceError as exc:
            raise _instance_not_found(exc.instance_id) from exc
        except InstanceNotFoundError as exc:
            raise _instance_not_found(str(exc)) from exc
        except MutationRejectedError as exc:
            raise PalmRestError(400, str(exc)) from exc
        except (TypeError, ValueError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def validate_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._ctx.definitions.validate_flow(body, runtime=self._ctx.runtime)
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

    def design_propose_flow(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self._ctx.design.propose_flow(body, base_flow_id=base_flow_id)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def design_publish_flow(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        from palm.common.services.errors import (
            DesignCommitRejectedServiceError,
            DesignProposalNotFoundServiceError,
        )

        try:
            return self._ctx.design.publish_flow(body, base_flow_id=base_flow_id)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(404, {"error": "proposal_not_found", "message": str(exc)}) from exc
        except DesignCommitRejectedServiceError as exc:
            raise PalmRestError(
                400,
                {
                    "error": "design_commit_rejected",
                    "message": exc.reason,
                    "blockers": exc.blockers,
                },
            ) from exc

    def design_propose_resource(
        self,
        body: dict[str, Any],
        *,
        base_resource_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self._ctx.design.propose_resource(body, base_resource_id=base_resource_id)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc

    def design_publish_resource(
        self,
        body: dict[str, Any],
        *,
        base_resource_id: str | None = None,
    ) -> dict[str, Any]:
        from palm.common.services.errors import (
            DesignCommitRejectedServiceError,
            DesignProposalNotFoundServiceError,
        )

        try:
            return self._ctx.design.publish_resource(body, base_resource_id=base_resource_id)
        except (TypeError, ValueError, KeyError) as exc:
            raise PalmRestError(400, str(exc)) from exc
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(404, {"error": "proposal_not_found", "message": str(exc)}) from exc
        except DesignCommitRejectedServiceError as exc:
            raise PalmRestError(
                400,
                {
                    "error": "design_commit_rejected",
                    "message": exc.reason,
                    "blockers": exc.blockers,
                },
            ) from exc

    def design_list_proposals(self, *, flow_id: str | None = None) -> dict[str, Any]:
        rows = self._ctx.design.list_proposals(flow_id=flow_id)
        params = PaginationParams(limit=max(len(rows), 1), offset=0)
        return list_envelope("proposals", rows, params)

    def design_get_proposal(self, proposal_id: str) -> dict[str, Any]:
        from palm.common.services.errors import DesignProposalNotFoundServiceError

        try:
            return self._ctx.design.get_proposal(proposal_id)
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "proposal_not_found",
                    "message": str(exc),
                    "proposal_id": proposal_id,
                },
            ) from exc

    def design_validate_proposal(self, proposal_id: str) -> dict[str, Any]:
        from palm.common.services.errors import DesignProposalNotFoundServiceError

        try:
            return self._ctx.design.validate_proposal(proposal_id, dry_run=True)
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "proposal_not_found",
                    "message": str(exc),
                    "proposal_id": proposal_id,
                },
            ) from exc

    def design_analyze_proposal_impact(self, proposal_id: str) -> dict[str, Any]:
        from palm.common.services.errors import (
            DesignCommitRejectedServiceError,
            DesignProposalNotFoundServiceError,
        )

        try:
            return self._ctx.design.analyze_proposal_impact(proposal_id)
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "proposal_not_found",
                    "message": str(exc),
                    "proposal_id": proposal_id,
                },
            ) from exc
        except DesignCommitRejectedServiceError as exc:
            raise PalmRestError(
                400,
                {
                    "error": "design_commit_rejected",
                    "message": exc.reason,
                    "proposal_id": proposal_id,
                    "blockers": exc.blockers,
                },
            ) from exc

    def design_commit_proposal(
        self,
        proposal_id: str,
        *,
        commit_token: str | None = None,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        from palm.common.services.errors import (
            DesignCommitRejectedServiceError,
            DesignProposalNotFoundServiceError,
        )

        try:
            return self._ctx.design.commit_proposal(
                proposal_id,
                commit_token=commit_token,
                input_token=input_token,
            )
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "proposal_not_found",
                    "message": str(exc),
                    "proposal_id": proposal_id,
                },
            ) from exc
        except DesignCommitRejectedServiceError as exc:
            raise PalmRestError(
                400,
                {
                    "error": "design_commit_rejected",
                    "message": exc.reason,
                    "proposal_id": proposal_id,
                    "blockers": exc.blockers,
                },
            ) from exc

    def design_discard_proposal(self, proposal_id: str) -> dict[str, Any]:
        from palm.common.services.errors import DesignProposalNotFoundServiceError

        try:
            return self._ctx.design.discard_proposal(proposal_id)
        except DesignProposalNotFoundServiceError as exc:
            raise PalmRestError(
                404,
                {
                    "error": "proposal_not_found",
                    "message": str(exc),
                    "proposal_id": proposal_id,
                },
            ) from exc

    def list_snapshots(self, instance_id: str) -> dict[str, Any]:
        try:
            snapshots = self._ctx.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))
        except InstanceNotFoundError as exc:
            raise _instance_not_found(instance_id) from exc

        rows = [snapshot_summary(index, snap) for index, snap in enumerate(snapshots)]
        params = PaginationParams(limit=100, offset=0)
        return list_envelope("snapshots", rows, params)

    def get_snapshot(self, instance_id: str, snapshot_id: str) -> dict[str, Any]:
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

        provider = body.get("provider")
        if not provider:
            try:
                described = self._ctx.definitions.get_resource(resource_ref)
            except Exception:
                described = {}
            provider = described.get("provider")

        return self._ctx.execution.providers.invoke(
            resource_ref,
            provider=str(provider) if provider else None,
            action=body.get("action"),
            params=body.get("params"),
            state=body.get("state"),
            resource_id=body.get("resource_id"),
        )


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


def _flow_id_from_submit_body(body: dict[str, Any]) -> str | None:
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
