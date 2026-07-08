"""Invoke adapters for the KV resource provider."""

from __future__ import annotations

from typing import Any

from palm.common.resource.document_storage import (
    StorageKvBackend,
    build_memory_key,
    build_memory_prefix,
    build_storage_key,
    build_storage_prefix,
    get_memory_kv_store,
    logical_keys_from_prefixed,
    resolve_kv_backend,
)
from palm.core.resource.result import ProviderResult
from palm.providers._registry import get_bound_runtime
from palm.providers.kv.flow.params import KvInvokeParams


def invoke_action(
    *,
    name: str,
    action: str,
    params: dict[str, Any] | None = None,
    resource_id: str | None = None,
) -> ProviderResult:
    invoke_params = KvInvokeParams.from_mapping(params)
    logical_key = str(resource_id or invoke_params.extras.get("key") or "").strip()
    runtime = get_bound_runtime()
    storage = runtime.storage if runtime is not None else None
    storage_backend_name = storage.backend_name if storage is not None else None

    try:
        backend_mode = resolve_kv_backend(
            invoke_params.backend,
            storage=storage,
            storage_backend_name=storage_backend_name,
        )
    except ValueError as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name)

    if action == "list":
        return _invoke_list(
            name=name,
            action=action,
            invoke_params=invoke_params,
            backend_mode=backend_mode,
            storage=storage,
        )

    if not logical_key:
        return ProviderResult.fail(
            "kv actions get/put/delete require resource_id (logical key)",
            action=action,
            provider=name,
        )

    if action == "get":
        return _invoke_get(
            name=name,
            action=action,
            invoke_params=invoke_params,
            logical_key=logical_key,
            backend_mode=backend_mode,
            storage=storage,
        )
    if action == "put":
        return _invoke_put(
            name=name,
            action=action,
            invoke_params=invoke_params,
            logical_key=logical_key,
            backend_mode=backend_mode,
            storage=storage,
        )
    if action == "delete":
        return _invoke_delete(
            name=name,
            action=action,
            invoke_params=invoke_params,
            logical_key=logical_key,
            backend_mode=backend_mode,
            storage=storage,
        )

    return ProviderResult.fail(
        f"Unsupported action {action!r}",
        action=action,
        provider=name,
        resource_id=logical_key,
    )


def _invoke_get(
    *,
    name: str,
    action: str,
    invoke_params: KvInvokeParams,
    logical_key: str,
    backend_mode: str,
    storage: Any,
) -> ProviderResult:
    if backend_mode == "memory":
        store = get_memory_kv_store()
        value = store.get(build_memory_key(invoke_params.namespace, logical_key))
    else:
        backend = StorageKvBackend(storage)
        value = backend.get(build_storage_key(invoke_params.namespace, logical_key))

    if value is None:
        return ProviderResult.ok(
            {
                "found": False,
                "value": invoke_params.default,
                "key": logical_key,
                "namespace": invoke_params.namespace,
                "backend": backend_mode,
            },
            action=action,
            provider=name,
            resource_id=logical_key,
        )
    return ProviderResult.ok(
        {
            "found": True,
            "value": value,
            "key": logical_key,
            "namespace": invoke_params.namespace,
            "backend": backend_mode,
        },
        action=action,
        provider=name,
        resource_id=logical_key,
    )


def _invoke_put(
    *,
    name: str,
    action: str,
    invoke_params: KvInvokeParams,
    logical_key: str,
    backend_mode: str,
    storage: Any,
) -> ProviderResult:
    if invoke_params.value is None:
        return ProviderResult.fail(
            "put requires params.value",
            action=action,
            provider=name,
            resource_id=logical_key,
        )

    if backend_mode == "memory":
        store = get_memory_kv_store()
        store.set(build_memory_key(invoke_params.namespace, logical_key), invoke_params.value)
    else:
        backend = StorageKvBackend(storage)
        backend.set(build_storage_key(invoke_params.namespace, logical_key), invoke_params.value)

    return ProviderResult.ok(
        {
            "written": True,
            "key": logical_key,
            "namespace": invoke_params.namespace,
            "backend": backend_mode,
        },
        action=action,
        provider=name,
        resource_id=logical_key,
    )


def _invoke_delete(
    *,
    name: str,
    action: str,
    invoke_params: KvInvokeParams,
    logical_key: str,
    backend_mode: str,
    storage: Any,
) -> ProviderResult:
    if backend_mode == "memory":
        store = get_memory_kv_store()
        deleted = store.delete(build_memory_key(invoke_params.namespace, logical_key))
    else:
        backend = StorageKvBackend(storage)
        deleted = backend.delete(build_storage_key(invoke_params.namespace, logical_key))

    return ProviderResult.ok(
        {
            "deleted": deleted,
            "key": logical_key,
            "namespace": invoke_params.namespace,
            "backend": backend_mode,
        },
        action=action,
        provider=name,
        resource_id=logical_key,
    )


def _invoke_list(
    *,
    name: str,
    action: str,
    invoke_params: KvInvokeParams,
    backend_mode: str,
    storage: Any,
) -> ProviderResult:
    if backend_mode == "memory":
        store = get_memory_kv_store()
        prefix = build_memory_prefix(invoke_params.namespace, invoke_params.prefix)
        full_keys = store.list_prefix(prefix)
        keys = logical_keys_from_prefixed(full_keys=full_keys, key_prefix=prefix)
    else:
        backend = StorageKvBackend(storage)
        prefix = build_storage_prefix(invoke_params.namespace, invoke_params.prefix)
        full_keys = backend.list_prefix(prefix)
        keys = logical_keys_from_prefixed(full_keys=full_keys, key_prefix=prefix)

    return ProviderResult.ok(
        {
            "keys": keys,
            "namespace": invoke_params.namespace,
            "prefix": invoke_params.prefix,
            "backend": backend_mode,
        },
        action=action,
        provider=name,
    )


__all__ = ["invoke_action"]