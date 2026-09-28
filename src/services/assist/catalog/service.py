"""Assist catalog subdomain — doctor, flows, waiting, discover."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.operator.waiting_jobs import enrich_job_list_rows, slim_waiting_job_row
from palm.core.orchestration import JobStatus
from services.assist.catalog.discover import discover as run_discover
from services.assist.catalog.menu import menu_for_assist
from services.assist.catalog.open import open_from_params

if TYPE_CHECKING:
    from services.assist.service import AssistService


class AssistCatalogService:
    """Read-only / health / menu surface for operators (tool-friendly)."""

    def __init__(self, assist: AssistService) -> None:
        self._assist = assist

    def doctor(self) -> dict[str, Any]:
        """Legacy anatomy packaging (OD-001) — prefer :meth:`top` / :meth:`vitality`."""
        return self._assist.inspect.doctor(self._assist.resolve_runtime())

    def top(self) -> dict[str, Any]:
        """Living load top — vitality projection via product inspect door."""
        return self._assist.inspect.top(self._assist.resolve_runtime())

    def vitality(self) -> dict[str, Any]:
        """Full vitality snapshot via product inspect door."""
        return self._assist.inspect.vitality(self._assist.resolve_runtime())

    def benchmark(
        self,
        *,
        recipe: str = "pulse",
        iterations: int = 10,
        store_full_snapshots: bool = False,
    ) -> dict[str, Any]:
        """Opt-in vitality benchmark via product inspect door (not everyday top)."""
        return self._assist.inspect.benchmark(
            self._assist.resolve_runtime(),
            recipe=recipe,
            iterations=iterations,
            store_full_snapshots=store_full_snapshots,
        )

    def list_flows(self) -> list[dict[str, Any]]:
        return self._assist.definitions.list_flows()

    def list_waiting(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """Jobs/instances waiting for interactive input (assist-only friendly)."""
        rows = self._assist.inspect.list_jobs(
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
        runtime = self._assist.resolve_runtime()
        if runtime is not None:
            out = enrich_job_list_rows(runtime, out)
        return [slim_waiting_job_row(row) for row in out]

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
