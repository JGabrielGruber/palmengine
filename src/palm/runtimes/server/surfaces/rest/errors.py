"""REST error helpers — thin wrappers over shared response envelopes."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse
from palm.common.runtimes.server.responses import error_response, unauthorized as _unauthorized


def bad_request(
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> ServerResponse:
    return error_response(400, "invalid_request", message, details=details, extra=extra)


def invalid_json(message: str = "request body must be valid JSON object") -> ServerResponse:
    return error_response(400, "invalid_json", message)


def empty_body() -> ServerResponse:
    return bad_request("request body is required")


def unauthorized() -> ServerResponse:
    from palm.common.runtimes.server.middleware import PALM_SUBJECT_HEADER

    return _unauthorized(f"missing or invalid {PALM_SUBJECT_HEADER} header")


def job_not_found(job_id: str) -> ServerResponse:
    return error_response(404, "job_not_found", f"Job not found: {job_id}", extra={"job_id": job_id})


def plan_not_found(plan_id: str) -> ServerResponse:
    return error_response(404, "plan_not_found", f"Plan not found: {plan_id}", extra={"plan_id": plan_id})


def instance_not_found(instance_id: str) -> ServerResponse:
    return error_response(
        404,
        "instance_not_found",
        f"Instance not found: {instance_id}",
        extra={"instance_id": instance_id},
    )


def submit_failed(detail: str) -> ServerResponse:
    return error_response(500, "submit_failed", detail)


def input_rejected(detail: str) -> ServerResponse:
    return error_response(400, "input_rejected", detail)


def resume_failed(detail: str) -> ServerResponse:
    return error_response(400, "resume_failed", detail)