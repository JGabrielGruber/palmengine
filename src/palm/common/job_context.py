"""
Job context assembly — rich REST read model beyond slim status.

Combines pattern inspection (provided by callers), wizard progress, instance
snapshots, and actionable next steps for human-first interactive flows.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.instances import ProcessInstance, StateSnapshot

_DEFAULT_MAX_EVENTS = 10


def instance_id_for_job(job: Job) -> str:
    """Resolve durable instance id from job metadata."""
    raw = job.metadata.get("instance_id")
    return str(raw) if raw else job.id


def build_job_context(
    job: Job,
    *,
    pattern: dict[str, Any],
    instance: ProcessInstance | None = None,
    wizard_progress: dict[str, Any] | None = None,
    resource_invocations: dict[str, Any] | None = None,
    max_events: int = _DEFAULT_MAX_EVENTS,
) -> dict[str, Any]:
    """Assemble a context-full job view for REST and operator tooling."""
    instance_id = instance_id_for_job(job)
    payload: dict[str, Any] = {
        "found": True,
        "job_id": job.id,
        "status": job.status.value,
        "metadata": dict(job.metadata),
        "pattern": pattern,
        "instance": _instance_block(instance_id, instance),
        "wizard_progress": wizard_progress,
        "resource_invocations": resource_invocations,
        "blackboard_snapshot": _latest_blackboard_snapshot(instance),
        "recent_events": _recent_events(
            instance,
            wizard_progress,
            resource_invocations,
            max_events=max_events,
        ),
        "next_actions": derive_next_actions(job.id, job.status, instance_id, instance),
    }
    if job.result is not None:
        payload["result"] = job.result
    if job.error is not None:
        payload["error"] = str(job.error)
    return payload


def derive_next_actions(
    job_id: str,
    status: JobStatus,
    instance_id: str,
    instance: ProcessInstance | None,
) -> list[dict[str, Any]]:
    """Suggest REST actions available from the current job state."""
    actions: list[dict[str, Any]] = []
    flow_id = _flow_id_for_instance(instance)

    if status == JobStatus.WAITING_FOR_INPUT and flow_id is not None:
        actions.append(
            {
                "action": "provide_input",
                "method": "POST",
                "path": f"/v1/api/flows/{flow_id}/session/{instance_id}/input",
                "description": "Deliver interactive wizard input",
            }
        )

    if instance is not None:
        actions.append(
            {
                "action": "get_instance",
                "method": "GET",
                "path": f"/v1/api/system/instances/{instance_id}",
                "description": "Inspect durable process instance",
            }
        )
        actions.append(
            {
                "action": "list_snapshots",
                "method": "GET",
                "path": f"/v1/api/system/instances/{instance_id}/snapshots",
                "description": "List point-in-time state snapshots",
            }
        )
        if status in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}:
            actions.append(
                {
                    "action": "resume_instance",
                    "method": "POST",
                    "path": f"/v1/api/system/instances/{instance_id}/resume",
                    "description": "Resume persisted process instance",
                }
            )

    actions.append(
        {
            "action": "get_job",
            "method": "GET",
            "path": f"/v1/api/system/jobs/{job_id}",
            "description": "Slim job status",
        }
    )
    actions.append(
        {
            "action": "inspect_job",
            "method": "GET",
            "path": f"/v1/api/system/jobs/{job_id}/context",
            "description": "Rich job context with pattern state and next actions",
        }
    )
    return actions


def _flow_id_for_instance(instance: ProcessInstance | None) -> str | None:
    if instance is None:
        return None
    if instance.flow_id:
        return str(instance.flow_id)
    if instance.flow_name:
        return str(instance.flow_name)
    flow_def = instance.flow_definition
    if isinstance(flow_def, dict):
        for key in ("id", "name", "flow_id"):
            value = flow_def.get(key)
            if value is not None:
                return str(value)
    return None


def _instance_block(instance_id: str, instance: ProcessInstance | None) -> dict[str, Any]:
    block: dict[str, Any] = {
        "instance_id": instance_id,
        "link": f"/v1/api/system/instances/{instance_id}",
    }
    if instance is not None:
        block["status"] = instance.status
        block["flow_name"] = instance.flow_name
        block["process_name"] = instance.process_name
        block["current_step_slug"] = instance.current_step_slug
    return block


def _latest_blackboard_snapshot(instance: ProcessInstance | None) -> dict[str, Any] | None:
    if instance is None or not instance.state_snapshots:
        return None
    index = len(instance.state_snapshots) - 1
    snapshot = instance.state_snapshots[index]
    return _snapshot_summary(index, snapshot)


def _snapshot_summary(index: int, snapshot: StateSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(index),
        "status": snapshot.status,
        "recorded_at": snapshot.recorded_at,
        "job_id": snapshot.job_id,
        "current_step_slug": snapshot.current_step_slug,
        "state_snapshot": dict(snapshot.state_snapshot),
    }


def _recent_events(
    instance: ProcessInstance | None,
    wizard_progress: dict[str, Any] | None,
    resource_invocations: dict[str, Any] | None,
    *,
    max_events: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    if instance is not None:
        for entry in instance.status_history:
            item: dict[str, Any] = {
                "type": "instance.status",
                "status": entry.status,
                "recorded_at": entry.recorded_at,
            }
            if entry.detail:
                item["detail"] = dict(entry.detail)
            events.append(item)

    if wizard_progress:
        trace = wizard_progress.get("backtrack_trace")
        if isinstance(trace, list):
            for entry in trace:
                if not isinstance(entry, dict):
                    continue
                events.append(
                    {
                        "type": str(entry.get("event_type", "wizard.backtrack")),
                        "recorded_at": entry.get("recorded_at"),
                        "from_step": entry.get("from_step"),
                        "to_step": entry.get("to_step"),
                        "blocked": entry.get("blocked"),
                        "reason": entry.get("reason"),
                    }
                )
        completed = wizard_progress.get("completed_steps")
        current = wizard_progress.get("current_step")
        if current:
            events.append(
                {
                    "type": "wizard.progress",
                    "recorded_at": wizard_progress.get("updated_at"),
                    "current_step": current,
                    "completed_steps": list(completed) if isinstance(completed, list) else [],
                }
            )

    if resource_invocations:
        entries = resource_invocations.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                events.append(
                    {
                        "type": str(entry.get("event_type", "resource.invoked")),
                        "recorded_at": entry.get("recorded_at"),
                        "resource_ref": entry.get("resource_ref"),
                        "action": entry.get("action"),
                        "step_slug": entry.get("step_slug"),
                        "success": entry.get("success"),
                    }
                )

    events = [event for event in events if event.get("recorded_at")]
    events.sort(key=lambda item: str(item.get("recorded_at", "")), reverse=True)
    return events[:max_events]
