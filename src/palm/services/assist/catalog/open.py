"""Assist open — start/inspect a catalog target (0.34)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.services.assist._params import want_input_schema, wizard_start_body
from palm.services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


def parse_open_token(value: str) -> tuple[str, str] | None:
    """Parse ``open:kind:id`` choice values from menu chips."""
    text = (value or "").strip()
    if not text.startswith("open:"):
        return None
    parts = text.split(":", 2)
    if len(parts) < 3:
        return None
    kind, iid = parts[1].strip(), parts[2].strip()
    if not kind or not iid:
        return None
    return kind, iid


def open_target(
    assist: AssistService,
    *,
    kind: str,
    target_id: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Open a menu target: flow session, scenario, session inspect, section, alias."""
    params = dict(params or {})
    kind_s = (kind or "").strip().lower()
    tid = (target_id or "").strip()
    if not tid:
        raise ValueError("open requires id")

    # Nested open:kind:id from chat value
    if tid.startswith("open:"):
        parsed = parse_open_token(tid)
        if parsed:
            kind_s, tid = parsed

    view_format = resolve_view_format(params)
    include_input = want_input_schema(params)

    if kind_s in {"section", "menu"}:
        from palm.services.assist.catalog.menu import menu_for_assist

        return menu_for_assist(
            assist,
            section=tid,
            query=str(params.get("query") or params.get("q") or ""),
            cursor=params.get("cursor"),
            limit=params.get("limit"),
        )

    if kind_s in {"flow", "flows"}:
        body = {"format": view_format}
        if include_input:
            body["include_input_schema"] = True
        # Prefer execution create via façade host path through execution service
        return assist.execution.flows.dispatch(
            ["flows", tid, "create"],
            body,
        )

    if kind_s in {"scenario", "scenarios"}:
        body = wizard_start_body(params)
        return assist.start_scenario(
            tid,
            body,
            view_format=view_format,
            include_input_schema=include_input,
        )

    if kind_s in {"session", "instance"}:
        return assist.sessions.inspect(
            tid,
            view_format=view_format,
            include_input_schema=include_input,
        )

    if kind_s in {"alias", "path"}:
        # Resolve via assist dispatch of alias-like path segments is caller's job;
        # here we map common aliases to concrete opens.
        if tid in {"assist/doctor", "doctor"}:
            return assist.doctor()
        if tid in {"assist/menu", "menu"}:
            from palm.services.assist.catalog.menu import menu_for_assist

            return menu_for_assist(assist, section="root")
        if tid.endswith("/start") or "/" not in tid:
            scenario = tid.split("/")[0] if "/" in tid else tid
            return assist.start_scenario(
                scenario,
                wizard_start_body(params),
                view_format=view_format,
                include_input_schema=include_input,
            )
        raise ValueError(f"unsupported open alias: {tid!r}")

    raise ValueError(f"unsupported open kind: {kind_s!r}")


def open_from_params(assist: AssistService, params: dict[str, Any] | None) -> Any:
    """Open from dispatch params (kind/id or value=open:…)."""
    params = dict(params or {})
    kind = params.get("kind") or params.get("open_kind")
    tid = params.get("id") or params.get("target_id") or params.get("target")
    value = params.get("value") or params.get("input")
    if (not kind or not tid) and isinstance(value, str):
        parsed = parse_open_token(value)
        if parsed:
            kind, tid = parsed
    if not kind and params.get("flow_id"):
        kind, tid = "flow", params.get("flow_id")
    if not kind and params.get("scenario_id"):
        kind, tid = "scenario", params.get("scenario_id")
    if not kind and params.get("session_id"):
        kind, tid = "session", params.get("session_id")
    if not kind or not tid:
        raise ValueError(
            "open requires kind+id, or value like open:flow:todo-builder, "
            "or flow_id / scenario_id / session_id"
        )
    return open_target(
        assist,
        kind=str(kind),
        target_id=str(tid),
        params=params,
    )


__all__ = [
    "open_from_params",
    "open_target",
    "parse_open_token",
]
