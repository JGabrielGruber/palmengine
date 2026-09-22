"""REST error helpers — thin wrappers over shared response envelopes."""

from __future__ import annotations

from typing import Any

from plugins.kits.server.protocol import ServerResponse
from plugins.kits.server.responses import error_response
from plugins.kits.server.responses import unauthorized as _unauthorized


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
    from plugins.kits.server.middleware import PALM_SUBJECT_HEADER

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


def admission_refused(detail: str) -> ServerResponse:
    """Organism gate closed — not a 500 bug and not a 400 validation error.

    Status **503** = service not ready for business (admission fail closed).
    Code **admission_refused** so clients distinguish gate from internal failure.
    """
    return error_response(503, "admission_refused", detail)


def capability_refused(detail: str) -> ServerResponse:
    """Organ missing after ready — not a 500 bug and not admission_refused.

    Status **409** = membership conflict (organism ready, organ not installed).
    Code **capability_refused** so clients do not mix the two questions.
    """
    return error_response(409, "capability_refused", detail)


def maybe_admission_refused(exc: BaseException) -> ServerResponse | None:
    """Map ready / organ refuse to honest REST voice; else ``None``.

    :class:`AdmissionRefusedError` → 503 ``admission_refused``.
    :class:`CapabilityRefusedError` → 409 ``capability_refused`` (0.67.4).
    Existing start/continue handlers already call this helper.
    """
    from palm.system.structure.errors import (
        AdmissionRefusedError,
        CapabilityRefusedError,
    )

    if isinstance(exc, AdmissionRefusedError):
        return admission_refused(str(exc))
    if isinstance(exc, CapabilityRefusedError):
        return capability_refused(str(exc))
    return None


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


def proposal_not_found(proposal_id: str) -> ServerResponse:
    return error_response(
        404,
        "proposal_not_found",
        f"Design proposal not found: {proposal_id}",
        extra={"proposal_id": proposal_id},
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
