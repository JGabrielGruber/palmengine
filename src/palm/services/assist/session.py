"""Assist session handles — thin shell over flow sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.core.orchestration import JobStatus
from palm.services.assist.schemas import AssistSessionContext, build_assist_session_context
from palm.services.execution.flows.schemas import SessionContext

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


class AssistSession:
    """Stateful handle for one assist scenario session."""

    def __init__(
        self,
        assist: AssistService,
        *,
        flow_id: str | None,
        session_id: str,
        scenario_id: str | None = None,
    ) -> None:
        self._assist = assist
        self.flow_id = flow_id
        self.session_id = session_id
        self.scenario_id = scenario_id

    def context(self, *, view_format: str = "assistant") -> AssistSessionContext:
        """Assist-enriched session view shaped for ``view_format`` on ``to_dict()``."""
        flow_ctx = self._flow_session().context()
        view = flow_ctx.detail if flow_ctx.detail else flow_ctx.to_dict()
        compact = compact_wizard_inspect(view)
        handoff_ready = _handoff_ready(flow_ctx)
        ctx = build_assist_session_context(
            session_id=self.session_id,
            flow_id=self.flow_id or flow_ctx.flow_id,
            view=view,
            scenario_id=self.scenario_id,
            operator_hint=compact.get("operator_hint"),
            handoff_ready=handoff_ready,
        )
        ctx.invoke_tree = _safe_invoke_tree(self._assist, self.session_id)
        return ctx

    def input(self, value: Any, *, view_format: str = "assistant") -> AssistSessionContext:
        self._flow_session().input(value)
        return self.context(view_format=view_format)

    def backtrack(self, to_step: str | None = None, *, view_format: str = "assistant") -> AssistSessionContext:
        self._flow_session().backtrack(to_step)
        return self.context(view_format=view_format)

    def resume(self) -> AssistSession:
        self._flow_session().resume()
        return self

    def cancel(self) -> dict[str, Any]:
        return self._flow_session().cancel()

    def _flow_session(self) -> Any:
        return self._assist.execution.flows.session(self.flow_id, self.session_id)


def _safe_invoke_tree(assist: Any, session_id: str) -> dict[str, Any] | None:
    try:
        return assist.invoke_tree(session_id)
    except Exception:
        return None


def _handoff_ready(flow_ctx: SessionContext) -> bool:
    status = flow_ctx.status
    if status == JobStatus.SUCCEEDED.value:
        return True
    prompt = flow_ctx.detail.get("prompt") if flow_ctx.detail else None
    if isinstance(prompt, dict) and prompt.get("step_kind") == "summary":
        return True
    return False


__all__ = ["AssistSession"]