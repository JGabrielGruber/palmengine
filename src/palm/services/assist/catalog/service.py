"""Assist catalog subdomain — doctor, flows, waiting, discover."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.services.assist.catalog.discover import discover as run_discover

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


class AssistCatalogService:
    """Read-only / health surface for operators (tool-friendly)."""

    def __init__(self, assist: AssistService) -> None:
        self._assist = assist

    def doctor(self) -> dict[str, Any]:
        return self._assist.system.doctor(self._assist.resolve_runtime())

    def list_flows(self) -> list[dict[str, Any]]:
        return self._assist.definitions.list_flows()

    def list_waiting(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """Jobs/instances waiting for interactive input (assist-only friendly)."""
        from palm.core.orchestration import JobStatus

        rows = self._assist.system.list_jobs(
            status=JobStatus.WAITING_FOR_INPUT.value,
            limit=limit,
        )
        out: list[dict[str, Any]] = []
        for row in rows or []:
            if hasattr(row, "to_dict"):
                out.append(row.to_dict())
            elif isinstance(row, dict):
                out.append(dict(row))
            else:
                out.append({"value": str(row)})
        return out

    def discover(self, query: str = "", *, limit: int = 12) -> dict[str, Any]:
        return run_discover(query, limit=limit)


__all__ = ["AssistCatalogService"]
