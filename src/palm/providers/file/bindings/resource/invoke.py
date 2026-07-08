"""Invoke adapters for the file document resource provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.common.resource.document_storage import FileDocumentStore, resolve_documents_root
from palm.core.exceptions import StoragePermissionError
from palm.core.resource.result import ProviderResult
from palm.providers._registry import get_bound_runtime
from palm.providers.file.flow.params import FileInvokeParams


def invoke_action(
    *,
    name: str,
    action: str,
    params: dict[str, Any] | None = None,
    resource_id: str | None = None,
) -> ProviderResult:
    invoke_params = FileInvokeParams.from_mapping(params)
    relative_path = str(resource_id or invoke_params.extras.get("path") or "").strip()

    try:
        store = _resolve_store(invoke_params)
    except (TypeError, ValueError, StoragePermissionError) as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name)

    if action == "list":
        return _invoke_list(
            name=name,
            action=action,
            invoke_params=invoke_params,
            store=store,
        )

    if not relative_path:
        return ProviderResult.fail(
            "file actions read/write/delete/exists require resource_id (relative path)",
            action=action,
            provider=name,
        )

    if action == "read":
        return _invoke_read(
            name=name,
            action=action,
            invoke_params=invoke_params,
            store=store,
            relative_path=relative_path,
        )
    if action == "write":
        return _invoke_write(
            name=name,
            action=action,
            invoke_params=invoke_params,
            store=store,
            relative_path=relative_path,
        )
    if action == "delete":
        return _invoke_delete(
            name=name,
            action=action,
            store=store,
            relative_path=relative_path,
        )
    if action == "exists":
        return _invoke_exists(
            name=name,
            action=action,
            store=store,
            relative_path=relative_path,
        )

    return ProviderResult.fail(
        f"Unsupported action {action!r}",
        action=action,
        provider=name,
        resource_id=relative_path,
    )


def _resolve_store(invoke_params: FileInvokeParams) -> FileDocumentStore:
    if invoke_params.documents_root:
        root = Path(str(invoke_params.documents_root))
    else:
        runtime = get_bound_runtime()
        if runtime is None:
            root = resolve_documents_root(object())
        else:
            root = resolve_documents_root(runtime)
    return FileDocumentStore(root)


def _invoke_read(
    *,
    name: str,
    action: str,
    invoke_params: FileInvokeParams,
    store: FileDocumentStore,
    relative_path: str,
) -> ProviderResult:
    try:
        content = store.read(relative_path, format=invoke_params.format)
    except (ValueError, StoragePermissionError) as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name, resource_id=relative_path)
    if content is None:
        return ProviderResult.fail(
            f"document not found: {relative_path}",
            action=action,
            provider=name,
            resource_id=relative_path,
        )
    return ProviderResult.ok(
        {
            "content": content,
            "path": relative_path,
            "documents_root": str(store.documents_root),
            "format": invoke_params.format,
        },
        action=action,
        provider=name,
        resource_id=relative_path,
    )


def _invoke_write(
    *,
    name: str,
    action: str,
    invoke_params: FileInvokeParams,
    store: FileDocumentStore,
    relative_path: str,
) -> ProviderResult:
    payload = invoke_params.write_payload
    if payload is None:
        return ProviderResult.fail(
            "write requires params.content or params.value",
            action=action,
            provider=name,
            resource_id=relative_path,
        )
    try:
        nbytes = store.write(relative_path, payload, format=invoke_params.format)
    except (ValueError, StoragePermissionError) as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name, resource_id=relative_path)
    return ProviderResult.ok(
        {
            "path": relative_path,
            "bytes": nbytes,
            "documents_root": str(store.documents_root),
            "format": invoke_params.format,
        },
        action=action,
        provider=name,
        resource_id=relative_path,
    )


def _invoke_delete(
    *,
    name: str,
    action: str,
    store: FileDocumentStore,
    relative_path: str,
) -> ProviderResult:
    try:
        deleted = store.delete(relative_path)
    except (ValueError, StoragePermissionError) as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name, resource_id=relative_path)
    return ProviderResult.ok(
        {
            "path": relative_path,
            "deleted": deleted,
            "documents_root": str(store.documents_root),
        },
        action=action,
        provider=name,
        resource_id=relative_path,
    )


def _invoke_exists(
    *,
    name: str,
    action: str,
    store: FileDocumentStore,
    relative_path: str,
) -> ProviderResult:
    try:
        exists = store.exists(relative_path)
    except (ValueError, StoragePermissionError) as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name, resource_id=relative_path)
    return ProviderResult.ok(
        {
            "path": relative_path,
            "exists": exists,
            "documents_root": str(store.documents_root),
        },
        action=action,
        provider=name,
        resource_id=relative_path,
    )


def _invoke_list(
    *,
    name: str,
    action: str,
    invoke_params: FileInvokeParams,
    store: FileDocumentStore,
) -> ProviderResult:
    try:
        paths = store.list(invoke_params.glob)
    except ValueError as exc:
        return ProviderResult.fail(str(exc), action=action, provider=name)
    return ProviderResult.ok(
        {
            "paths": paths,
            "glob": invoke_params.glob,
            "documents_root": str(store.documents_root),
        },
        action=action,
        provider=name,
    )


__all__ = ["invoke_action"]