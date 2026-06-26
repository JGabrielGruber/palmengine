"""
Wizard CQRS handler dispatch — command and query branches for the host bus.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import SubmitFlowCommand
from palm.common.cqrs.query import GetInstanceStatusQuery, ListInstancesQuery
from palm.common.interactive_runtime import (
    provide_interactive_input_for_instance,
    request_interactive_backtrack_for_instance,
)
from palm.common.patterns.pattern_read_model import build_pattern_read_model
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
    SubmitWizardCommand,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    GetWizardStatusQuery,
    ListWizardProgressQuery,
)

if TYPE_CHECKING:
    from palm.common.cqrs.command import Command
    from palm.common.cqrs.query import Query
    from palm.patterns.wizard.bindings.cqrs.projection import WizardProgressProjection


def _resolve_runtime(ctx: Any, runtime_name: str | None) -> Any:
    router = getattr(ctx, "_router", None)
    app = getattr(ctx, "_app", None)
    if app is not None and router is not None:
        resolved = router.route_job_runtime(runtime_name)
        return app.runtime(resolved)
    runtime = getattr(ctx, "_runtime", None)
    if runtime is not None:
        return runtime
    raise RuntimeError("CQRS context has no runtime resolution path")


def handle_wizard_command(command: Command, ctx: Any) -> Any | None:
    """Dispatch wizard commands; return ``None`` when ``command`` is not wizard-owned."""
    if isinstance(command, SubmitWizardCommand):
        submit = SubmitFlowCommand(
            flow=wizard_flow_payload(command.body),
            runtime_name=command.runtime_name,
            by_id=bool(command.body.get("by_id", False)),
            job_id=_optional_str(command.body.get("job_id")),
        )
        if hasattr(ctx, "handle"):
            return ctx.handle(submit)
        if hasattr(ctx, "_submit_flow"):
            return ctx._submit_flow(submit)
        raise RuntimeError("CQRS context cannot submit wizard flows")
    if isinstance(command, ProvideWizardInputCommand):
        runtime = _resolve_runtime(ctx, command.runtime_name)
        job, slug = provide_interactive_input_for_instance(
            runtime,
            command.instance_id,
            command.value,
        )
        return {
            "instance_id": command.instance_id,
            "job_id": job.id,
            "slug": slug,
        }
    if isinstance(command, RequestWizardBacktrackCommand):
        runtime = _resolve_runtime(ctx, command.runtime_name)
        job, to_step = request_interactive_backtrack_for_instance(
            runtime,
            command.instance_id,
            command.to_step,
        )
        return {
            "instance_id": command.instance_id,
            "job_id": job.id,
            "to_step": to_step,
        }
    return None


def handle_wizard_query(query: Query, ctx: Any) -> Any | None:
    """Dispatch wizard queries; return ``None`` when ``query`` is not wizard-owned."""
    if isinstance(query, GetWizardProgressQuery):
        wizard_progress = ctx._pattern_projections.get("wizard")
        if wizard_progress is not None:
            return wizard_progress.get_progress(query)
        if hasattr(ctx, "_wizard_progress"):
            return ctx._wizard_progress(
                instance_id=query.instance_id,
                job_id=query.job_id,
            )
        return None
    if isinstance(query, ListWizardProgressQuery):
        wizard_progress = ctx._pattern_projections.get("wizard")
        if wizard_progress is None:
            return []
        rows = wizard_progress.list_progress(query)
        if not query.active_only:
            return rows
        instances = getattr(ctx, "_instances", None)
        if instances is None:
            return rows
        active_ids = {
            row.instance_id
            for row in instances.list_instances(
                ListInstancesQuery(include_terminal=False)
            )
        }
        return [row for row in rows if row.instance_id in active_ids]
    if isinstance(query, GetWizardStatusQuery):
        return get_wizard_status(query, ctx)
    return None


def get_wizard_status(query: GetWizardStatusQuery, ctx: Any) -> dict[str, Any] | None:
    instances = getattr(ctx, "_instances", None)
    if instances is not None:
        instance = instances.get_instance(GetInstanceStatusQuery(instance_id=query.instance_id))
        if instance is None:
            return None
        instance_payload = instance.to_dict()
        job_id = instance.job_id
    elif hasattr(ctx, "_get_instance"):
        instance_payload = ctx._get_instance(
            GetInstanceStatusQuery(instance_id=query.instance_id)
        )
        if instance_payload is None:
            return None
        job_id = str(instance_payload.get("job_id") or query.instance_id)
    else:
        return None

    wizard_progress = None
    wizard_progress_proj = ctx._pattern_projections.get("wizard")
    if wizard_progress_proj is not None:
        progress = wizard_progress_proj.get_progress(
            GetWizardProgressQuery(instance_id=query.instance_id, job_id=job_id)
        )
        wizard_progress = progress.to_dict() if progress is not None else None
    elif hasattr(ctx, "_wizard_progress"):
        wizard_progress = ctx._wizard_progress(
            instance_id=query.instance_id,
            job_id=job_id,
        )

    pattern: dict[str, Any] | None = None
    job_status: str | None = None
    job_result: Any = None
    try:
        if hasattr(ctx, "_app"):
            job = ctx._app.runtime().get_job(job_id)
        else:
            job = ctx._runtime.get_job(job_id)
        job_status = job.status.value
        job_result = job.result
        from palm.runtimes.cli.shared.job_inspect import inspect_job_json

        inspected = inspect_job_json(job)
        if inspected.get("pattern") == "wizard":
            pattern = inspected
    except Exception:
        pass

    return build_pattern_read_model(
        "wizard",
        instance_payload,
        wizard_progress=wizard_progress,
        pattern=pattern,
        job_status=job_status,
        job_result=job_result,
    )


def wizard_flow_payload(body: dict[str, Any]) -> dict[str, Any] | str:
    if "wizard" in body:
        payload: dict[str, Any] = {"wizard": body["wizard"]}
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return payload
    if "flow" in body and isinstance(body["flow"], dict):
        flow = dict(body["flow"])
        pattern = flow.get("pattern")
        if pattern not in (None, "wizard"):
            raise ValueError("flow.pattern must be 'wizard'")
        flow["pattern"] = "wizard"
        payload = {"flow": flow}
        if body.get("job_id") is not None:
            payload["job_id"] = body["job_id"]
        return payload
    if "flow_name" in body:
        return str(body["flow_name"])
    raise ValueError("expected 'wizard', 'flow', or 'flow_name' in request body")


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = [
    "get_wizard_status",
    "handle_wizard_command",
    "handle_wizard_query",
    "wizard_flow_payload",
]