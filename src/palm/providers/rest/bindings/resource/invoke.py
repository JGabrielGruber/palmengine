"""Invoke adapters for the REST resource provider."""

from __future__ import annotations

from typing import Any

from palm.core.resource.result import ProviderResult
from palm.providers.rest.bindings.transport.http import http_request
from palm.providers.rest.exceptions import RestRemoteError
from palm.providers.rest.flow.params import RestInvokeParams


def fetch_resource(
    *,
    name: str,
    resource_id: str,
    params: dict[str, Any] | None = None,
) -> ProviderResult:
    """Fetch a remote resource via HTTP GET."""
    invoke_params = RestInvokeParams.from_mapping(params)
    try:
        url = invoke_params.resolve_url(resource_id)
    except ValueError as exc:
        return ProviderResult.fail(str(exc), action="fetch", provider=name, resource_id=resource_id)

    try:
        status, payload = http_request(
            invoke_params.method,
            url,
            headers=invoke_params.headers,
            timeout=invoke_params.timeout,
            retries=invoke_params.retries,
        )
    except RestRemoteError as exc:
        return ProviderResult.fail(
            str(exc),
            action="fetch",
            provider=name,
            resource_id=resource_id,
            status_code=exc.status_code,
        )

    return ProviderResult.ok(
        {
            "id": resource_id,
            "url": url,
            "status_code": status,
            "body": payload,
        },
        action="fetch",
        provider=name,
        resource_id=resource_id,
    )


def invoke_action(
    *,
    name: str,
    action: str,
    params: dict[str, Any] | None = None,
    resource_id: str | None = None,
) -> ProviderResult:
    if action == "fetch":
        rid = str(resource_id or (params or {}).get("resource_id") or "").strip()
        if not rid:
            return ProviderResult.fail(
                "fetch requires resource_id",
                action=action,
                provider=name,
            )
        return fetch_resource(name=name, resource_id=rid, params=params)
    return ProviderResult.fail(
        f"Unsupported action {action!r}",
        action=action,
        provider=name,
        resource_id=resource_id,
    )
