"""Flow execution MCP tools — command-path session operator API."""

from __future__ import annotations

from typing import Any

from palm.common.operator.collection_drive import COLLECTION_ADD_ONE_SHOT, drive_collection_add
from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.drive_inputs import drive_wizard_inputs
from palm.common.operator.input_coercion import resolve_mcp_wizard_input
from palm.common.operator.compose_status import build_compose_status
from palm.common.operator.flow_session_view import shape_flow_session_view
from palm.common.operator.view_registry import normalize_view_format
from palm.runtimes.mcp.flows.views import (
    ensure_flow_id,
    flatten_session_view,
    submission_view,
)
from palm.runtimes.mcp.rest_client import PalmRestError
from palm.runtimes.mcp.descriptions import tool_description
from palm.runtimes.mcp.submit_body import submit_body

_PALM_FLOWS_SESSION_DESC = tool_description(
    "palm_flows_session",
    "Inspect a running flow session (powertool by default).",
    when=(
        "Pass ``format=assistant`` for human-readable turns with ``question``, "
        "``choices``, and ``actions``. Re-inspect after every input — never guess state."
    ),
    examples=[
        'palm_flows_session(session_id="inst-xxx", format="assistant")',
        'palm_flows_session(session_id="inst-xxx")',
        'palm_flows_session(session_id="inst-xxx", flow_id="todo-builder", include=["validation"])',
    ],
    use_instead=(
        "To send input and get the next turn, use ``palm_assist(params={session_id, flow_id, value})`` "
        "or ``palm_flows_session_input``."
    ),
)

_PALM_FLOWS_SESSION_INPUT_DESC = tool_description(
    "palm_flows_session_input",
    "Deliver interactive wizard input for a flow session.",
    when="Use plain ``input`` strings (``yes``, choice slugs, text) — not JSON answer blobs.",
    examples=[
        'palm_flows_session_input(session_id="inst-xxx", input="yes")',
        'palm_flows_session_input(session_id="inst-xxx", input="todo-builder")',
        'palm_flows_session_input(session_id="inst-xxx", input="add", value="Buy milk")',
    ],
    use_instead="Prefer ``palm_assist(params={session_id, flow_id, value})`` for unified driving.",
)

_PALM_FLOWS_LIST_DESC = tool_description(
    "palm_flows_list",
    "List runnable flows from the execution catalog.",
    when="Use at session start to discover available wizards, or read ``palm://definitions/flows``.",
    examples=[
        "palm_flows_list()",
    ],
)

_PALM_FLOWS_CREATE_SESSION_DESC = tool_description(
    "palm_flows_create_session",
    "Start a new flow session; returns ``session_id`` and ``job_id``.",
    when="For interactive entry, prefer ``palm_assist(path=[\"flows\", \"<flow>\", \"create\"])``.",
    examples=[
        'palm_flows_create_session(flow_id="todo-builder")',
        'palm_flows_create_session(flow_id="approval")',
    ],
)


def register_flow_tools(mcp: Any, backend: Any) -> None:
    """Register flow session MCP tools (0.16 command-path vocabulary)."""

    def _format_session_payload(
        flat: dict[str, Any],
        *,
        session_id: str,
        flow_id: str | None,
        format: str = "powertool",
    ) -> dict[str, Any]:
        invoke_tree = None
        if normalize_view_format(format) == "assistant":
            invoke_tree = backend.get_instance_tree(session_id)
        fid = flow_id or flat.get("flow_name") or flat.get("flow")
        return shape_flow_session_view(
            flat,
            format=format,
            session_id=session_id,
            flow_id=str(fid) if fid is not None else None,
            path=(
                ["flows", str(fid), "session", session_id]
                if fid is not None
                else ["flows", "session", session_id]
            ),
            invoke_tree=invoke_tree,
        )

    @mcp.tool(description=_PALM_FLOWS_LIST_DESC)
    def palm_flows_list() -> dict[str, Any]:
        return backend.flows_list()

    @mcp.tool
    def palm_flows_describe(flow_id: str) -> dict[str, Any]:
        """Describe one flow (catalog row)."""
        return backend.flows_describe(flow_id)

    @mcp.tool(description=_PALM_FLOWS_CREATE_SESSION_DESC)
    def palm_flows_create_session(
        flow_id: str,
        wizard: dict[str, Any] | None = None,
        flow: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        body = submit_body(flow_name=flow_id, wizard=wizard, flow=flow, job_id=job_id)
        return backend.flows_create_session(flow_id, body)

    @mcp.tool(description=_PALM_FLOWS_SESSION_DESC)
    def palm_flows_session(
        session_id: str,
        flow_id: str | None = None,
        format: str = "powertool",
        include: list[str] | None = None,
        truncate_answers_at: int = 2000,
    ) -> dict[str, Any]:
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

    @mcp.tool(description=_PALM_FLOWS_SESSION_INPUT_DESC)
    def palm_flows_session_input(
        session_id: str,
        input: str | None = None,
        value: str | int | float | bool | None = None,
        flow_id: str | None = None,
        format: str = "powertool",
    ) -> dict[str, Any]:
        inspect = flatten_session_view(backend.flows_get_session(flow_id, session_id))
        resolved = resolve_mcp_wizard_input(input=input, value=value, wizard_view=inspect)
        fid = ensure_flow_id(flow_id=flow_id, session_id=session_id, inspect=inspect)
        if (
            isinstance(resolved, tuple)
            and len(resolved) == 2
            and resolved[0] == COLLECTION_ADD_ONE_SHOT
        ):

            def provide(field_value: Any) -> dict[str, Any]:
                raw_view = backend.flows_session_input(fid, session_id, field_value)
                return flatten_session_view(raw_view)

            flat = drive_collection_add(
                provide,
                value=resolved[1],
                wizard_view=inspect,
            )
            return _format_session_payload(
                flat,
                session_id=session_id,
                flow_id=fid,
                format=format,
            )
        view = backend.flows_session_input(fid, session_id, resolved)
        return _format_session_payload(
            flatten_session_view(view),
            session_id=session_id,
            flow_id=fid,
            format=format,
        )

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