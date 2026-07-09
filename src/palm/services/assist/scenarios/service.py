"""Assist scenarios subdomain — list / describe / start / inspect-catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery
from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.services.assist.registry import list_scenario_rows, scenario_by_id
from palm.services.assist.session import AssistSession
from palm.services.assist.views import resolve_view_format
from palm.services.definitions.flows import flow_catalog_row

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


class AssistScenarioService:
    """Operator / design entry scenarios (registry + flow start)."""

    def __init__(self, assist: AssistService) -> None:
        self._assist = assist

    def list(self) -> list[dict[str, Any]]:
        return list_scenario_rows()

    def describe(self, scenario_id: str) -> dict[str, Any]:
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        row: dict[str, Any] = {
            "scenario_id": contributor.scenario_id,
            "flow_id": contributor.flow_id,
            "summary": contributor.summary,
            "contributor_id": contributor.contributor_id,
        }
        flow = self._assist.ask(GetFlowQuery(flow_id=contributor.flow_id))
        if flow is not None:
            row["flow"] = flow_catalog_row(flow)
        return row

    def start(
        self,
        scenario_id: str,
        body: dict[str, Any],
        *,
        view_format: str = "assistant",
        include_input_schema: bool = False,
    ) -> dict[str, Any]:
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        run_body = {**body, "flow_name": contributor.flow_id, "by_id": True}
        session = self._assist.execution.flows.run_wizard(run_body)
        handle = AssistSession(
            self._assist,
            flow_id=contributor.flow_id,
            session_id=session.session_id,
            scenario_id=scenario_id,
        )
        return handle.context(view_format=view_format, sync_gate=True).to_dict(
            view_format=view_format,
            include_input_schema=include_input_schema,
        )

    def inspect_catalog(
        self,
        scenario_id: str,
        *,
        view_format: str = "assistant",
    ) -> dict[str, Any]:
        """Read-only operator catalog — no session mutation."""
        contributor = scenario_by_id(scenario_id)
        if contributor is None:
            raise DefinitionNotFoundServiceError("scenario", scenario_id)
        from palm.core.orchestration import JobStatus

        flows = self._assist.catalog.list_flows()
        waiting = self._assist.system.list_instances(
            status=JobStatus.WAITING_FOR_INPUT.value,
            include_terminal=False,
            limit=50,
        )
        waiting_rows: list[dict[str, Any]] = []
        for row in waiting:
            if hasattr(row, "to_dict"):
                waiting_rows.append(row.to_dict())
            elif isinstance(row, dict):
                waiting_rows.append(dict(row))
        payload: dict[str, Any] = {
            "scenario_id": scenario_id,
            "operator_mode": "inspect",
            "status": "catalog",
            "question": "Read-only operator catalog.",
            "hint": (
                "Use list flows / list waiting tools. Start a scenario only when the user asks."
            ),
            "flows": flows,
            "waiting": waiting_rows,
            "mutation": {
                "mutations_allowed": False,
                "requires_user_input": False,
                "agent_hint": "Read-only catalog — do not send value/input.",
            },
            "actions": [
                {
                    "label": "Publish new flow (one call)",
                    "alias": "design/publish",
                },
                {
                    "label": "Publish resource (one call)",
                    "alias": "design/publish-resource",
                },
                {
                    "label": "Start coconut NPC",
                    "tool": "palm_assist",
                    "params": {"flow_id": "coconut-npc"},
                },
                {"label": "List flows", "alias": "assist/catalog/flows"},
                {"label": "Doctor (resource preflight)", "alias": "assist/doctor"},
                {"label": "List waiting sessions", "alias": "assist/catalog/waiting"},
                {
                    "label": "Start operator entry",
                    "alias": "operator-entry/start",
                },
            ],
        }
        if resolve_view_format({"format": view_format}) != "assistant":
            payload["format"] = view_format
        return payload


__all__ = ["AssistScenarioService"]
