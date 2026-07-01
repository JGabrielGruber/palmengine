"""Flow execution MCP tools — command-path session operator API."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.drive_inputs import drive_wizard_inputs
from palm.common.operator.input_coercion import resolve_mcp_wizard_input
from palm.common.operator.compose_status import build_compose_status
from palm.common.operator.view_registry import normalize_view_format
from palm.runtimes.mcp.flows.views import (
    ensure_flow_id,
    flatten_session_view,
    shape_flow_session_view,
    submission_view,
)
from palm.runtimes.mcp.rest_client import PalmRestError
from palm.runtimes.mcp.submit_body import submit_body


def register_flow_tools(mcp: Any, backend: Any) -> None:
    """Register flow session MCP tools (0.16 command-path vocabulary)."""

    @mcp.tool
    def palm_flows_list() -> dict[str, Any]:
        """List runnable flows from the execution flows catalog."""
        return backend.flows_list()

    @mcp.tool
    def palm_flows_describe(flow_id: str) -> dict[str, Any]:
        """Describe one flow (catalog row)."""
        return backend.flows_describe(flow_id)

    @mcp.tool
    def palm_flows_create_session(
        flow_id: str,
        wizard: dict[str, Any] | None = None,
        flow: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a flow session; returns session_id and job_id."""
        body = submit_body(flow_name=flow_id, wizard=wizard, flow=flow, job_id=job_id)
        return backend.flows_create_session(flow_id, body)

    @mcp.tool
    def palm_flows_session(
        session_id: str,
        flow_id: str | None = None,
        format: str = "powertool",
        include: list[str] | None = None,
        truncate_answers_at: int = 2000,
    ) -> dict[str, Any]:
        """Inspect a flow session (powertool by default; ``format=assistant`` opt-in)."""
        view = backend.flows_get_session(flow_id, session_id)
        flat = flatten_session_view(view)
        invoke_tree = None
        if normalize_view_format(format) == "assistant":
            invoke_tree = backend.get_instance_tree(session_id)
        return shape_flow_session_view(
            flat,
            format=format,
            session_id=session_id,
            flow_id=flow_id,
            invoke_tree=invoke_tree,
            include=include,
            truncate_answers_at=truncate_answers_at,
        )

    @mcp.tool
    def palm_flows_session_input(
        session_id: str,
        input: str | None = None,
        value: str | int | float | bool | None = None,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Deliver interactive input. Use plain ``input`` strings—not JSON."""
        inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
        resolved = resolve_mcp_wizard_input(input=input, value=value, wizard_view=inspect)
        fid = ensure_flow_id(flow_id=flow_id, session_id=session_id, inspect=inspect)
        view = backend.flows_session_input(fid, session_id, resolved)
        return compact_wizard_inspect(flatten_session_view(view))

    @mcp.tool
    def palm_flows_session_resume_child_wait(
        session_id: str,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Re-check nested child flow and advance parent when ready."""
        try:
            inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
            fid = ensure_flow_id(flow_id=flow_id, session_id=session_id, inspect=inspect)
            view = backend.flows_session_resume_child_wait(fid, session_id)
        except PalmRestError as exc:
            if exc.status != 400 or "not waiting for a nested child" not in str(exc).lower():
                raise
            inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
            payload = compact_wizard_inspect(inspect)
            payload["resume_child_wait"] = "skipped_not_waiting"
            return payload
        return compact_wizard_inspect(flatten_session_view(view))

    @mcp.tool
    def palm_flows_session_drive(
        session_id: str,
        inputs: list[str] | None = None,
        max_steps: int = 30,
        payload: dict[str, Any] | None = None,
        include_steps: bool = False,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply multiple session inputs in one call; stops on wait/child-wait/terminal."""
        if not inputs and payload is None:
            raise ValueError("provide at least one of inputs or payload")

        def get_session(sid: str) -> dict[str, Any]:
            return flatten_session_view(backend.flows_get_session(flow_id, sid))

        def provide_input(sid: str, value: Any) -> dict[str, Any]:
            inspect = get_session(sid)
            fid = ensure_flow_id(flow_id=flow_id, session_id=sid, inspect=inspect)
            view = backend.flows_session_input(fid, sid, value)
            return flatten_session_view(view)

        return drive_wizard_inputs(
            instance_id=session_id,
            inputs=inputs or [],
            get_wizard=get_session,
            provide_input=provide_input,
            max_steps=max_steps,
            payload=payload,
            include_steps=include_steps,
            include_operator_hint=False,
        )

    @mcp.tool
    def palm_flows_session_resume(
        session_id: str,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Re-drive a waiting interactive flow (for example auto-run a resource step)."""
        inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
        fid = ensure_flow_id(flow_id=flow_id, session_id=session_id, inspect=inspect)
        view = backend.flows_session_resume(fid, session_id)
        return compact_wizard_inspect(flatten_session_view(view))

    @mcp.tool
    def palm_flows_session_backtrack(
        session_id: str,
        to_step: str | None = None,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Backtrack a session to a prior step (omit to_step for previous step)."""
        inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
        fid = ensure_flow_id(flow_id=flow_id, session_id=session_id, inspect=inspect)
        view = backend.flows_session_backtrack(fid, session_id, to_step=to_step)
        return compact_wizard_inspect(flatten_session_view(view))

    @mcp.tool
    def palm_flows_compose_status(
        session_id: str,
        flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Compositional session summary: invoke stack, step, answers, and operator_hint."""
        tree = backend.get_instance_tree(session_id)
        inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
        compact = compact_wizard_inspect(inspect, include_operator_hint=False)
        return build_compose_status(tree, compact)


__all__ = ["register_flow_tools"]