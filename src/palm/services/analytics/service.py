"""AnalyticsService — thin BI query/present (0.35.2 skeleton)."""

from __future__ import annotations

import time
from typing import Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.base import BaseService
from palm.services.analytics.datasets import list_datasets, resolve_dataset
from palm.services.analytics.errors import (
    AnalyticsDisabledError,
    AnalyticsError,
    AnalyticsResponseTooLargeError,
    DatasetNotFoundError,
)
from palm.services.analytics.normalize import (
    apply_limit,
    apply_select,
    coerce_rows,
    estimate_bytes,
    extract_payload,
)
from palm.services.analytics.present.pipeline import present

_PROFILES = frozenset({"raw", "table", "series", "kpi"})


class AnalyticsService(BaseService):
    """Read-only BI path: gate → invoke → normalize → present. Not a warehouse."""

    def __init__(
        self,
        *,
        definitions: Any,
        providers: Any,
        commands: CommandBus | None = None,
        queries: QueryBus | None = None,
        schemas: CqrsSchemaRegistry | None = None,
        allow_unpublished: bool = False,
        default_limit: int = 1000,
        max_limit: int = 10_000,
        max_response_bytes: int = 2_000_000,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            commands=commands or CommandBus(),
            queries=queries or QueryBus(),
            schemas=schemas or CqrsSchemaRegistry(),
        )
        self._definitions = definitions
        self._providers = providers
        self._allow_unpublished = allow_unpublished
        self._default_limit = default_limit
        self._max_limit = max_limit
        self._max_response_bytes = max_response_bytes
        self._enabled = enabled

    def list_datasets(self, *, published_only: bool = True) -> list[dict[str, Any]]:
        self._require_enabled()
        return list_datasets(self._definitions, published_only=published_only)

    def describe(self, dataset: str) -> dict[str, Any]:
        self._require_enabled()
        detail, exposure = resolve_dataset(
            self._definitions,
            dataset,
            allow_unpublished=self._allow_unpublished,
        )
        name = str(detail.get("name") or dataset)
        return {
            "status": "ok",
            "dataset": name,
            "schema": {
                "input_schema": detail.get("input_schema"),
                "output_schema": detail.get("output_schema"),
            },
            "exposure": exposure.to_dict(),
            "lineage": {
                "kind": exposure.kind,
                "derived_from": list(exposure.derived_from),
                "resource_ref": name,
                "provider": detail.get("provider"),
                "action": detail.get("action"),
            },
        }

    def query(
        self,
        dataset: str,
        *,
        profile: str = "table",
        params: dict[str, Any] | None = None,
        select: list[str] | None = None,
        limit: int | None = None,
        series: dict[str, Any] | None = None,
        kpi: dict[str, Any] | None = None,
        runtime_name: str | None = None,
    ) -> dict[str, Any]:
        """Gate → invoke → normalize (rows→select→limit) → present."""
        self._require_enabled()
        profile_s = str(profile or "table").strip().lower() or "table"
        if profile_s not in _PROFILES:
            return self._error(
                dataset,
                f"Unknown profile {profile!r}",
                code="invalid_profile",
            )

        try:
            detail, exposure = resolve_dataset(
                self._definitions,
                dataset,
                allow_unpublished=self._allow_unpublished,
            )
        except AnalyticsError as exc:
            return self._error(dataset, str(exc), code=exc.code)

        name = str(detail.get("name") or dataset)
        t0 = time.perf_counter()
        try:
            envelope = self._providers.invoke(
                name,
                params=dict(params or {}),
                runtime_name=runtime_name,
            )
        except Exception as exc:  # noqa: BLE001 — surface as invoke_failed
            return self._error(name, str(exc), code="invoke_failed")

        if not isinstance(envelope, dict):
            return self._error(name, "Invalid provider envelope", code="invoke_failed")

        invoke_ms = int((time.perf_counter() - t0) * 1000)
        if not envelope.get("success", False):
            err = envelope.get("error") or "invoke failed"
            return self._error(name, str(err), code="invoke_failed")

        t1 = time.perf_counter()
        payload = extract_payload(envelope, row_path=exposure.row_path)

        if profile_s == "raw":
            data = present("raw", payload=payload)
            size = estimate_bytes(data)
            if size > self._max_response_bytes:
                return self._error(
                    name,
                    f"Response too large ({size} > {self._max_response_bytes})",
                    code="response_too_large",
                )
            present_ms = int((time.perf_counter() - t1) * 1000)
            return self._ok(
                name,
                profile_s,
                data=data,
                exposure=exposure,
                detail=detail,
                meta={
                    "row_count": None,
                    "truncated": False,
                    "limit": None,
                    "invoke_ms": invoke_ms,
                    "present_ms": present_ms,
                },
            )

        rows = coerce_rows(payload)
        rows = apply_select(rows, select)
        req_limit = self._default_limit if limit is None else limit
        rows, applied_limit, truncated = apply_limit(
            rows, limit=req_limit, max_limit=self._max_limit
        )
        size = estimate_bytes(rows)
        if size > self._max_response_bytes:
            return self._error(
                name,
                f"Response too large ({size} > {self._max_response_bytes})",
                code="response_too_large",
            )
        data = present(profile_s, rows=rows, series=series, kpi=kpi)
        present_ms = int((time.perf_counter() - t1) * 1000)
        return self._ok(
            name,
            profile_s,
            data=data,
            exposure=exposure,
            detail=detail,
            meta={
                "row_count": len(rows),
                "truncated": truncated,
                "limit": applied_limit,
                "invoke_ms": invoke_ms,
                "present_ms": present_ms,
            },
        )

    def _require_enabled(self) -> None:
        if not self._enabled:
            raise AnalyticsDisabledError()

    def _ok(
        self,
        dataset: str,
        profile: str,
        *,
        data: dict[str, Any],
        exposure: Any,
        detail: dict[str, Any],
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "ok",
            "dataset": dataset,
            "profile": profile,
            "schema": {
                "input_schema": detail.get("input_schema"),
                "output_schema": detail.get("output_schema"),
            },
            "lineage": {
                "kind": exposure.kind,
                "derived_from": list(exposure.derived_from),
                "resource_ref": dataset,
                "provider": detail.get("provider"),
                "action": detail.get("action"),
            },
            "meta": meta,
            "data": data,
        }

    def _error(self, dataset: str, message: str, *, code: str) -> dict[str, Any]:
        return {
            "status": "error",
            "dataset": str(dataset or ""),
            "error": message,
            "code": code,
        }


__all__ = ["AnalyticsService"]
