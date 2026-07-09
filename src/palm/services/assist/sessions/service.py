"""Assist sessions subdomain — open handle, verbs, handoff, invoke tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.operator.invoke_tree import build_invoke_tree
from palm.services.assist._params import want_input_schema
from palm.services.assist._view_meta import flow_id_from_view, scenario_id_from_view
from palm.services.assist.session import AssistSession
from palm.services.assist.sessions.handoff import resolve_handoff
from palm.services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


class AssistSessionService:
    """Drive an assist/flow instance (inspect, input, back, resume, cancel, handoff)."""

    def __init__(self, assist: AssistService) -> None:
        self._assist = assist

    def get(self, session_id: str) -> AssistSession:
        view = self._assist.system.inspect_instance(session_id)
        flow_id = flow_id_from_view(view)
        scenario_id = scenario_id_from_view(view, flow_id)
        return AssistSession(
            self._assist,
            flow_id=flow_id,
            session_id=session_id,
            scenario_id=scenario_id,
        )

    def inspect(
        self,
        session_id: str,
        *,
        view_format: str = "assistant",
        include_input_schema: bool = False,
    ) -> dict[str, Any]:
        return (
            self.get(session_id)
            .context(view_format=view_format, sync_gate=True)
            .to_dict(
                view_format=view_format,
                include_input_schema=include_input_schema,
            )
        )

    def apply_verb(
        self,
        session_id: str,
        verb: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Apply a session verb and return a shaped dict (or cancel/handoff payload)."""
        params = params or {}
        view_format = resolve_view_format(params)
        include_input = want_input_schema(params)
        handle = self.get(session_id)
        if verb == "input":
            value = params.get("value", params.get("input"))
            return handle.input(
                value,
                params=params,
                view_format=view_format,
            ).to_dict(view_format=view_format, include_input_schema=include_input)
        if verb == "backtrack":
            return handle.backtrack(params.get("to_step"), view_format=view_format).to_dict(
                view_format=view_format,
                include_input_schema=include_input,
            )
        if verb == "resume":
            handle.resume()
            return handle.context(view_format=view_format, sync_gate=True).to_dict(
                view_format=view_format,
                include_input_schema=include_input,
            )
        if verb == "cancel":
            return handle.cancel()
        if verb == "handoff":
            return self.handoff(session_id)
        raise RuntimeError(f"unknown assist session verb: {verb}")

    def handoff(self, session_id: str) -> dict[str, Any]:
        return resolve_handoff(self._assist, session_id)

    def invoke_tree(self, session_id: str) -> dict[str, Any]:
        return build_invoke_tree(
            self._assist.resolve_runtime(),
            session_id,
            base_url=None,
        )


__all__ = ["AssistSessionService"]
