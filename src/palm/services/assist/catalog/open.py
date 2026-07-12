"""Assist open — start/inspect a catalog target (0.34)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.services.assist._params import want_input_schema, wizard_start_body
from palm.services.assist.views import resolve_view_format

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


def _as_mapping(result: Any) -> Any:
    if result is None:
        return None
    if isinstance(result, dict):
        return dict(result)
    if hasattr(result, "to_dict"):
        data = result.to_dict()
        return dict(data) if isinstance(data, dict) else data
    return result


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
        body: dict[str, Any] = {"format": view_format}
        if include_input:
            body["include_input_schema"] = True
        # Create then re-inspect so chat gets question + input schema (0.34.5+)
        created = _as_mapping(
            assist.execution.flows.dispatch(
                ["flows", tid, "create"],
                body,
            )
        )
        session_id = None
        if isinstance(created, dict):
            session_id = created.get("session_id") or created.get("instance_id")
        if session_id:
            inspect_path = ["flows", tid, "session", str(session_id)]
            try:
                inspected = _as_mapping(
                    assist.execution.flows.dispatch(
                        inspect_path,
                        {
                            "format": view_format,
                            **({"include_input_schema": True} if include_input else {}),
                        },
                    )
                )
                if isinstance(inspected, dict):
                    inspected.setdefault("flow_id", tid)
                    refs = inspected.get("refs")
                    if not isinstance(refs, dict):
                        refs = {}
                        inspected["refs"] = refs
                    refs.setdefault("flow_id", tid)
                    # Help shapers treat this as a flow session even under path assist/open
                    inspected["_open_flow_path"] = inspect_path
                return inspected
            except Exception:
                if isinstance(created, dict):
                    created.setdefault("flow_id", tid)
                return created
        return created

    if kind_s in {"scenario", "scenarios"}:
        body = wizard_start_body(params)
        return assist.start_scenario(
            tid,
            body,
            view_format=view_format,
            include_input_schema=include_input,
        )

    if kind_s in {"session", "instance"}:
        # Optional resume verb before inspect (0.34.5)
        action = str(params.get("action") or params.get("verb") or "").lower()
        if action in {"resume", "continue"}:
            try:
                return assist.sessions.apply_verb(tid, "resume", params)
            except Exception:
                pass
        view = assist.sessions.inspect(
            tid,
            view_format=view_format,
            include_input_schema=include_input,
        )
        # Attach flow_id from params or inspect for Portal bind
        if isinstance(view, dict):
            flow = params.get("flow_id") or view.get("flow_id")
            refs = view.get("refs") if isinstance(view.get("refs"), dict) else {}
            if not flow and refs.get("flow_id"):
                flow = refs["flow_id"]
            if flow:
                view = dict(view)
                view.setdefault("flow_id", flow)
                r = dict(view.get("refs") or {})
                r.setdefault("flow_id", flow)
                view["refs"] = r
            # Human CTA if still waiting
            status = str(view.get("status") or "").lower()
            if status in {"waiting", "waiting_for_input"}:
                actions = list(view.get("actions") or [])
                labels = {str(a.get("label") or "").lower() for a in actions if isinstance(a, dict)}
                if "resume session" not in labels and "continue" not in labels:
                    actions.insert(
                        0,
                        {
                            "label": "Continue answering",
                            "alias": "assist/open",
                            "params": {
                                "kind": "session",
                                "id": tid,
                                **({"flow_id": flow} if flow else {}),
                            },
                        },
                    )
                    view = dict(view)
                    view["actions"] = actions
        return view

    if kind_s in {"dataset", "datasets", "analytics"}:
        return _open_dataset(assist, tid, params)

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


def _open_dataset(
    assist: AssistService,
    dataset: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Describe (+ optional preview query) a published analytics dataset (0.40.4)."""
    name = (dataset or "").strip()
    analytics = getattr(assist, "analytics", None)
    profile = str(params.get("profile") or "table").strip() or "table"
    want_preview = str(params.get("preview") or params.get("query") or "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    preview_limit = 20
    try:
        preview_limit = max(1, min(100, int(params.get("limit") or 20)))
    except (TypeError, ValueError):
        preview_limit = 20

    if analytics is None:
        # Fallback: resolve definition only (no query path)
        from palm.services.analytics.datasets import resolve_dataset

        try:
            detail, exposure = resolve_dataset(assist.definitions, name)
        except Exception as exc:
            return {
                "path": ["assist", "open", "dataset", name],
                "status": "error",
                "kind": "dataset",
                "dataset": name,
                "error": str(exc),
                "question": f"Dataset {name!r} unavailable.",
                "hint": "Publish the resource with metadata.analytics.published=true.",
            }
        return {
            "path": ["assist", "open", "dataset", name],
            "status": "ok",
            "kind": "dataset",
            "dataset": name,
            "describe": {
                "dataset": name,
                "kind": exposure.kind,
                "default_profile": exposure.default_profile,
                "exposure": exposure.to_public_dict(),
                "resource": {
                    "name": detail.get("name"),
                    "provider": detail.get("provider"),
                    "action": detail.get("action"),
                },
            },
            "question": f"Dataset {name} ({exposure.kind}). AnalyticsService not bound — describe only.",
            "hint": "Wire host analytics or use GET /v1/api/analytics/datasets/{name}.",
            "actions": [
                {
                    "label": "Analytics datasets",
                    "alias": "assist/menu",
                    "params": {"section": "datasets"},
                }
            ],
        }

    try:
        desc = analytics.describe(name)
    except Exception as exc:
        return {
            "path": ["assist", "open", "dataset", name],
            "status": "error",
            "kind": "dataset",
            "dataset": name,
            "error": str(exc),
            "question": f"Could not describe {name!r}: {exc}",
            "hint": "Check publication and read action allowlist.",
            "actions": [
                {
                    "label": "Analytics datasets",
                    "alias": "assist/menu",
                    "params": {"section": "datasets"},
                }
            ],
        }

    out: dict[str, Any] = {
        "path": ["assist", "open", "dataset", name],
        "status": "ok",
        "kind": "dataset",
        "dataset": name,
        "describe": desc if isinstance(desc, dict) else {"raw": desc},
        "question": _dataset_question(name, desc if isinstance(desc, dict) else {}),
        "hint": "Preview uses AnalyticsService.query. Menu · datasets for more.",
        "actions": [
            {
                "label": "Query table",
                "alias": "assist/open",
                "params": {
                    "kind": "dataset",
                    "id": name,
                    "profile": "table",
                    "preview": "1",
                },
            },
            {
                "label": "Query series",
                "alias": "assist/open",
                "params": {
                    "kind": "dataset",
                    "id": name,
                    "profile": "series",
                    "preview": "1",
                },
            },
            {
                "label": "Analytics datasets",
                "alias": "assist/menu",
                "params": {"section": "datasets"},
            },
            {
                "label": "Menu home",
                "alias": "assist/menu",
                "params": {},
            },
        ],
    }

    if want_preview:
        try:
            preview = analytics.query(
                name,
                profile=profile,
                limit=preview_limit,
            )
            if isinstance(preview, dict):
                out["preview"] = preview
                out["profile"] = profile
                # Surface a short row count for chat
                data = preview.get("data") if isinstance(preview.get("data"), dict) else preview
                if isinstance(data, dict) and "rows" in data:
                    out["hint"] = (
                        f"Preview profile={profile!r} · {len(data.get('rows') or [])} row(s) "
                        f"(limit {preview_limit})."
                    )
        except Exception as exc:
            out["preview_error"] = str(exc)
            out["hint"] = f"Describe ok; preview failed: {exc}"

    return out


def _dataset_question(name: str, desc: dict[str, Any]) -> str:
    kind = desc.get("kind") or desc.get("exposure", {}).get("kind") if isinstance(
        desc.get("exposure"), dict
    ) else desc.get("kind")
    fields = desc.get("fields") or []
    nfields = len(fields) if isinstance(fields, list) else 0
    bits = [f"Dataset **{name}**"]
    if kind:
        bits.append(f"kind={kind}")
    if nfields:
        bits.append(f"{nfields} field(s)")
    if desc.get("virtual") or (
        isinstance(desc.get("exposure"), dict) and desc["exposure"].get("source")
    ):
        bits.append("virtual view")
    return " · ".join(bits)


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
    if not kind and params.get("dataset"):
        kind, tid = "dataset", params.get("dataset")
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
