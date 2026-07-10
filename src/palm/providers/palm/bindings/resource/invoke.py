"""Invoke and fetch adapters for the Palm compositional provider."""

from __future__ import annotations

import uuid
from typing import Any

from palm.core.resource.observability import execution_block_from_state
from palm.core.resource.result import ProviderResult
from palm.providers.palm.bindings.recursion.guard import PalmRecursionError
from palm.providers.palm.exceptions import PalmProviderError, PalmTimeoutError
from palm.providers.palm.flow.coordinator import PalmInvokeCoordinator
from palm.providers.palm.bindings.resource.system_inspect import (
    invoke_system_read,
    is_system_read_action,
)
from palm.providers.palm.flow.params import PalmInvokeParams
from palm.providers.palm.flow.target import parse_target


def invoke_action(
    coordinator: PalmInvokeCoordinator,
    *,
    name: str,
    action: str,
    params: dict[str, Any] | None = None,
    resource_id: str | None = None,
    execution_state: Any | None = None,
    **kwargs: Any,
) -> ProviderResult:
    """Execute a named Palm provider action and return a structured result."""
    invoke_params = PalmInvokeParams.from_mapping(
        params,
        resource_id=resource_id,
        **kwargs,
    )
    invoke_params = inject_parent_job_from_state(invoke_params, execution_state)

    action_s = str(action or "").strip()
    if action_s == "fetch":
        return fetch_job(
            coordinator, name, action_s, invoke_params, resource_id=resource_id
        )

    if is_system_read_action(action_s):
        return invoke_system_read(
            name=name,
            action=action_s,
            params=invoke_params,
            resource_id=resource_id,
        )

    try:
        target = parse_target(
            action=action_s,
            resource_id=resource_id,
            params=invoke_params.as_target_dict(),
        )
    except ValueError as exc:
        return _fail(name, action_s, str(exc), resource_id=resource_id)

    try:
        payload = coordinator.invoke(action_s, target, invoke_params)
    except PalmRecursionError as exc:
        return _fail(name, action_s, str(exc), resource_id=resource_id)
    except PalmTimeoutError as exc:
        return _fail(name, action_s, str(exc), resource_id=resource_id)
    except PalmProviderError as exc:
        return _fail(name, action_s, str(exc), resource_id=resource_id)

    return ProviderResult.ok(
        payload,
        action=action_s,
        provider=name,
        resource_id=resource_id or target.ref,
        mode="remote" if invoke_params.is_remote else "local",
        invoke_depth=payload.get("invoke_depth"),
        parent_job_id=invoke_params.parent_job_id,
        wait_mode=invoke_params.resolved_wait_mode.value,
        waiting_for_child_wizard=payload.get("waiting_for_child_wizard"),
        child_job_id=payload.get("child_job_id"),
        child_instance_id=payload.get("child_instance_id"),
    )


def fetch_job(
    coordinator: PalmInvokeCoordinator,
    name: str,
    action: str,
    params: PalmInvokeParams,
    *,
    resource_id: str | None,
) -> ProviderResult:
    """Fetch a job snapshot by id."""
    job_id = params.resolve_job_id(resource_id=resource_id)
    if not job_id:
        return _fail(
            name,
            action,
            "fetch requires job_id or resource_id",
            resource_id=resource_id,
        )
    try:
        payload = coordinator.fetch(params, resource_id=resource_id)
    except PalmProviderError as exc:
        return _fail(name, action, str(exc), resource_id=job_id)
    return ProviderResult.ok(
        payload,
        action=action,
        provider=name,
        resource_id=job_id,
        mode="remote" if params.is_remote else "local",
    )


def inject_parent_job_from_state(
    params: PalmInvokeParams,
    execution_state: Any | None,
) -> PalmInvokeParams:
    """Inject parent job correlation from execution state when absent."""
    if params.parent_job_id:
        return params
    block = execution_block_from_state(execution_state)
    if not block.get("job_id"):
        block = execution_block_from_state(params.resolve_state())
    parent_job_id = block.get("job_id")
    if not parent_job_id:
        return params
    params.parent_job_id = str(parent_job_id)
    return params


def new_child_job_id(prefix: str = "palm-child") -> str:
    """Generate a correlation-friendly child job id."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _fail(
    name: str,
    action: str,
    message: str,
    *,
    resource_id: str | None,
) -> ProviderResult:
    return ProviderResult.fail(
        message,
        action=action,
        provider=name,
        resource_id=resource_id,
    )
