"""Assist catalog subdomain — doctor, flows, waiting, discover."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.services.assist.catalog.discover import discover as run_discover
from palm.services.assist.catalog.menu import menu_for_assist
from palm.services.assist.catalog.open import open_from_params

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


class AssistCatalogService:
    """Read-only / health / menu surface for operators (tool-friendly)."""

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

    def menu(
        self,
        *,
        section: str = "root",
        query: str = "",
        cursor: object | None = None,
        limit: object | None = None,
    ) -> dict[str, Any]:
        return menu_for_assist(
            self._assist,
            section=section,
            query=query,
            cursor=cursor,
            limit=limit,
        )

    def open(self, params: dict[str, Any] | None = None) -> Any:
        return open_from_params(self._assist, params)


__all__ = ["AssistCatalogService"]
