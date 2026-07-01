"""REST error helpers — thin wrappers over shared response envelopes."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse
from palm.common.runtimes.server.responses import error_response
from palm.common.runtimes.server.responses import unauthorized as _unauthorized


def bad_request(
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> ServerResponse:
    return error_response(400, "invalid_request", message, details=details, extra=extra)


def validation_failed(details: list[dict[str, Any]]) -> ServerResponse:
    """Schema validation failure with per-field detail entries."""
    message = "request validation failed"
    if details:
        message = details[0]["message"]
    return error_response(400, "validation_failed", message, details=details)


def invalid_json(message: str = "request body must be valid JSON object") -> ServerResponse:
    return error_response(400, "invalid_json", message)


def empty_body() -> ServerResponse:
    return bad_request("request body is required")


def unauthorized() -> ServerResponse:
    from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER

    return _unauthorized(f"missing or invalid {PALM_SUBJECT_HEADER} header")


def job_not_found(job_id: str) -> ServerResponse:
    return error_response(
        404, "job_not_found", f"Job not found: {job_id}", extra={"job_id": job_id}
    )


def plan_not_found(plan_id: str) -> ServerResponse:
    return error_response(
        404, "plan_not_found", f"Plan not found: {plan_id}", extra={"plan_id": plan_id}
    )


def instance_not_found(instance_id: str) -> ServerResponse:
    return error_response(
        404,
        "instance_not_found",
        f"Instance not found: {instance_id}",
        extra={"instance_id": instance_id},
    )


def wizard_not_found(instance_id: str) -> ServerResponse:
    return error_response(
        404,
        "wizard_not_found",
        f"Wizard not found: {instance_id}",
        extra={"instance_id": instance_id},
    )


def submit_failed(detail: str) -> ServerResponse:
    return error_response(500, "submit_failed", detail)


def input_rejected(detail: str) -> ServerResponse:
    return error_response(400, "input_rejected", detail)


def backtrack_rejected(detail: str) -> ServerResponse:
    return error_response(400, "backtrack_rejected", detail)


def resume_failed(detail: str) -> ServerResponse:
    return error_response(400, "resume_failed", detail)


def snapshot_not_found(instance_id: str, snapshot_id: str) -> ServerResponse:
    return error_response(
        404,
        "snapshot_not_found",
        f"Snapshot not found: {snapshot_id}",
        extra={"instance_id": instance_id, "snapshot_id": snapshot_id},
    )


def scenario_not_found(scenario_id: str) -> ServerResponse:
    return error_response(
        404,
        "scenario_not_found",
        f"Assist scenario not found: {scenario_id}",
        extra={"scenario_id": scenario_id},
    )


def flow_not_found(flow_id: str) -> ServerResponse:
    return error_response(
        404,
        "flow_not_found",
        f"Flow not found: {flow_id}",
        extra={"flow_id": flow_id},
    )


def process_not_found(process_id: str) -> ServerResponse:
    return error_response(
        404,
        "process_not_found",
        f"Process not found: {process_id}",
        extra={"process_id": process_id},
    )


def resource_not_found(resource_ref: str) -> ServerResponse:
    return error_response(
        404,
        "resource_not_found",
        f"Resource not found: {resource_ref}",
        extra={"resource_ref": resource_ref},
    )
