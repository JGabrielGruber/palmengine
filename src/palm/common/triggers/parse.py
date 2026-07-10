"""Parse definition trigger metadata (0.37)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TriggerKind = Literal["schedule", "on_flow", "on_resource"]


@dataclass(frozen=True, slots=True)
class TriggerSpec:
    kind: TriggerKind
    work_flow_id: str
    coalesce_key: str | None = None
    # schedule
    interval_seconds: int | None = None
    # on_flow
    source_flow: str | None = None
    when: str = "succeeded"
    # on_resource
    resource: str | None = None
    actions: tuple[str, ...] = ()
    debounce_seconds: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


def parse_triggers(metadata: dict[str, Any] | None) -> list[TriggerSpec]:
    """Parse ``metadata.triggers`` list; also map ``analytics.refresh.flow_id``."""
    if not isinstance(metadata, dict):
        return []
    out: list[TriggerSpec] = []
    raw_list = metadata.get("triggers")
    if isinstance(raw_list, list):
        for item in raw_list:
            if isinstance(item, dict):
                spec = _parse_one(item)
                if spec is not None:
                    out.append(spec)
    # analytics.refresh.flow_id → on_resource-less schedule/manual refresh target
    analytics = metadata.get("analytics")
    if isinstance(analytics, dict):
        refresh = analytics.get("refresh")
        if isinstance(refresh, dict):
            flow_id = refresh.get("flow_id")
            if flow_id:
                out.append(
                    TriggerSpec(
                        kind="schedule",
                        work_flow_id=str(flow_id),
                        coalesce_key=f"refresh:{flow_id}",
                        interval_seconds=int(refresh["interval_seconds"])
                        if refresh.get("interval_seconds") is not None
                        else None,
                        raw={"from": "analytics.refresh"},
                    )
                )
    return out


def _parse_one(item: dict[str, Any]) -> TriggerSpec | None:
    kind = str(item.get("kind") or "").strip().lower()
    work = item.get("work") if isinstance(item.get("work"), dict) else {}
    flow_id = str(
        work.get("flow_id") or item.get("flow_id") or item.get("target") or ""
    ).strip()
    if not flow_id and kind != "on_flow":
        # on_flow may default work to a fixed target in work.flow_id only
        pass
    coalesce = work.get("coalesce_key") or item.get("coalesce_key")
    coalesce_s = str(coalesce) if coalesce else None

    if kind == "schedule":
        if not flow_id:
            return None
        interval = item.get("interval_seconds")
        try:
            interval_i = int(interval) if interval is not None else None
        except (TypeError, ValueError):
            interval_i = None
        return TriggerSpec(
            kind="schedule",
            work_flow_id=flow_id,
            coalesce_key=coalesce_s or f"schedule:{flow_id}",
            interval_seconds=interval_i,
            raw=dict(item),
        )

    if kind == "on_flow":
        source = str(item.get("flow") or item.get("source_flow") or "").strip()
        when = str(item.get("when") or "succeeded").strip().lower()
        target = flow_id or str(work.get("flow_id") or "").strip()
        if not source or not target:
            return None
        return TriggerSpec(
            kind="on_flow",
            work_flow_id=target,
            coalesce_key=coalesce_s or f"on_flow:{source}:{target}",
            source_flow=source,
            when=when,
            raw=dict(item),
        )

    if kind == "on_resource":
        resource = str(item.get("resource") or "").strip()
        if not resource or not flow_id:
            return None
        actions_raw = item.get("actions") or ["put"]
        if isinstance(actions_raw, str):
            actions = (actions_raw.lower(),)
        elif isinstance(actions_raw, list):
            actions = tuple(str(a).lower() for a in actions_raw if a)
        else:
            actions = ("put",)
        try:
            debounce = float(item.get("debounce") or item.get("debounce_seconds") or 0)
        except (TypeError, ValueError):
            debounce = 0.0
        return TriggerSpec(
            kind="on_resource",
            work_flow_id=flow_id,
            coalesce_key=coalesce_s or f"on_resource:{resource}:{flow_id}",
            resource=resource,
            actions=actions or ("put",),
            debounce_seconds=debounce,
            raw=dict(item),
        )

    return None


__all__ = ["TriggerKind", "TriggerSpec", "parse_triggers"]
