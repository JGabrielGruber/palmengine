"""AnalyticsService — thin BI query/present (0.35–0.36)."""

from __future__ import annotations

import time
from typing import Any

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.common.services.base import BaseService
from palm.services.analytics.datasets import list_datasets, resolve_dataset
from palm.services.analytics.errors import AnalyticsDisabledError, AnalyticsError
from palm.services.analytics.normalize import (
    apply_limit,
    apply_select,
    coerce_rows,
    estimate_bytes,
    extract_payload,
)
from palm.services.analytics.present.pipeline import present
from palm.services.analytics.schema_roles import fields_from_schemas
from palm.services.analytics.virtual import apply_view_transform

_PROFILES = frozenset({"raw", "table", "series", "kpi"})


class AnalyticsService(BaseService):
    """Read-only BI path: gate → invoke (or virtual) → normalize → present."""

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
        fields = fields_from_schemas(
            output_schema=detail.get("output_schema")
            if isinstance(detail.get("output_schema"), dict)
            else None,
            analytics_fields=[dict(f) for f in exposure.fields] or None,
        )
        return {
            "status": "ok",
            "dataset": name,
            "schema": {
                "input_schema": detail.get("input_schema"),
                "output_schema": detail.get("output_schema"),
            },
            "fields": fields,
            "exposure": exposure.to_dict(),
            "lineage": self._lineage(name, exposure, detail),
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
        self._require_enabled()
        profile_s = str(profile or "table").strip().lower() or "table"
        if profile_s not in _PROFILES:
            return self._error(
                dataset, f"Unknown profile {profile!r}", code="invalid_profile"
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
            if exposure.is_virtual:
                envelope, row_path, lineage_extra = self._invoke_virtual(
                    exposure, params=params, runtime_name=runtime_name
                )
            else:
                envelope = self._providers.invoke(
                    name,
                    params=dict(params or {}),
                    runtime_name=runtime_name,
                )
                row_path = exposure.row_path
                lineage_extra = {}
        except AnalyticsError as exc:
            return self._error(name, str(exc), code=exc.code)
        except Exception as exc:  # noqa: BLE001
            return self._error(name, str(exc), code="invoke_failed")

        if not isinstance(envelope, dict):
            return self._error(name, "Invalid provider envelope", code="invoke_failed")

        invoke_ms = int((time.perf_counter() - t0) * 1000)
        if not envelope.get("success", False):
            err = envelope.get("error") or "invoke failed"
            return self._error(name, str(err), code="invoke_failed")

        t1 = time.perf_counter()
        payload = extract_payload(envelope, row_path=row_path)

        if exposure.is_virtual and profile_s != "raw":
            try:
                rows = coerce_rows(payload)
                rows = apply_view_transform(rows, exposure.transform)
                payload = rows
            except ValueError as exc:
                return self._error(name, str(exc), code="virtual_transform_failed")

        if profile_s == "raw":
            if exposure.is_virtual:
                try:
                    rows = coerce_rows(
                        extract_payload(envelope, row_path=row_path)
                    )
                    payload = apply_view_transform(rows, exposure.transform)
                except ValueError as exc:
                    return self._error(name, str(exc), code="virtual_transform_failed")
            data = present("raw", payload=payload)
            return self._finish_ok(
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
                    "present_ms": int((time.perf_counter() - t1) * 1000),
                    "virtual": exposure.is_virtual,
                },
                lineage_extra=lineage_extra,
            )

        rows = coerce_rows(payload) if not isinstance(payload, list) else [
            r if isinstance(r, dict) else {"value": r} for r in payload
        ]
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            rows = [dict(r) for r in payload if isinstance(r, dict)]

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
        return self._finish_ok(
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
                "present_ms": int((time.perf_counter() - t1) * 1000),
                "virtual": exposure.is_virtual,
            },
            lineage_extra=lineage_extra,
        )

    def _invoke_virtual(
        self,
        exposure: Any,
        *,
        params: dict[str, Any] | None,
        runtime_name: str | None,
    ) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
        source = str(exposure.source or "").strip()
        if not source:
            raise AnalyticsError(
                "Virtual view missing source",
                code="virtual_source_failed",
                http_status=400,
            )
        source_detail, source_exp = resolve_dataset(
            self._definitions,
            source,
            allow_unpublished=self._allow_unpublished,
        )
        source_name = str(source_detail.get("name") or source)
        envelope = self._providers.invoke(
            source_name,
            params=dict(params or {}),
            runtime_name=runtime_name,
        )
        if not isinstance(envelope, dict):
            raise AnalyticsError(
                "Invalid source envelope",
                code="virtual_source_failed",
                http_status=502,
            )
        lineage = {
            "source": source_name,
            "derived_from": list(exposure.derived_from)
            or ([source_name] if source_name else []),
        }
        return envelope, source_exp.row_path, lineage

    def _require_enabled(self) -> None:
        if not self._enabled:
            raise AnalyticsDisabledError()

    def _lineage(
        self, dataset: str, exposure: Any, detail: dict[str, Any]
    ) -> dict[str, Any]:
        derived = list(exposure.derived_from)
        if exposure.source and exposure.source not in derived:
            derived = derived or [exposure.source]
        return {
            "kind": exposure.kind,
            "derived_from": derived,
            "resource_ref": dataset,
            "provider": detail.get("provider"),
            "action": detail.get("action"),
            "source": exposure.source,
            "virtual": exposure.is_virtual,
        }

    def _finish_ok(
        self,
        dataset: str,
        profile: str,
        *,
        data: dict[str, Any],
        exposure: Any,
        detail: dict[str, Any],
        meta: dict[str, Any],
        lineage_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        lineage = self._lineage(dataset, exposure, detail)
        if lineage_extra:
            lineage.update({k: v for k, v in lineage_extra.items() if v is not None})
        fields = fields_from_schemas(
            output_schema=detail.get("output_schema")
            if isinstance(detail.get("output_schema"), dict)
            else None,
            analytics_fields=[dict(f) for f in exposure.fields] or None,
        )
        return {
            "status": "ok",
            "dataset": dataset,
            "profile": profile,
            "schema": {
                "input_schema": detail.get("input_schema"),
                "output_schema": detail.get("output_schema"),
            },
            "fields": fields,
            "lineage": lineage,
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
