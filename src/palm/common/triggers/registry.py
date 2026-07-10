"""Match live events to WorkIntents from definition triggers."""

from __future__ import annotations

from typing import Any

from palm.common.triggers.parse import TriggerSpec, parse_triggers
from palm.core.work import WorkIntent


class TriggerRegistry:
    """In-memory trigger index reloaded from flow definition metadata."""

    def __init__(self) -> None:
        self._specs: list[tuple[str, TriggerSpec]] = []  # (owner_flow_name, spec)
        self._schedule_last: dict[str, float] = {}

    def reload_from_flow_rows(
        self,
        flow_rows: list[dict[str, Any]],
        *,
        get_metadata: Any = None,
    ) -> int:
        """
        Load triggers.

        ``flow_rows`` thin catalog rows with name. Optional ``get_metadata(name)``
        returns full metadata dict (N+1). If absent, uses row['metadata'].
        """
        self._specs.clear()
        count = 0
        for row in flow_rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("flow_id") or "").strip()
            if not name:
                continue
            meta = None
            if callable(get_metadata):
                try:
                    meta = get_metadata(name)
                except Exception:
                    meta = None
            if meta is None:
                meta = row.get("metadata")
            if not isinstance(meta, dict):
                continue
            for spec in parse_triggers(meta):
                self._specs.append((name, spec))
                count += 1
        return count

    def on_event(self, event_type: str, payload: dict[str, Any]) -> list[WorkIntent]:
        et = str(event_type or "")
        out: list[WorkIntent] = []
        for _owner, spec in self._specs:
            intent = self._match(spec, et, payload)
            if intent is not None:
                out.append(intent)
        return out

    def due_schedules(self, *, now_ts: float) -> list[WorkIntent]:
        """Emit intents for schedule triggers whose interval has elapsed."""
        out: list[WorkIntent] = []
        for _owner, spec in self._specs:
            if spec.kind != "schedule":
                continue
            interval = spec.interval_seconds
            if interval is None or interval < 0:
                continue
            key = spec.coalesce_key or spec.work_flow_id
            last = self._schedule_last.get(key, 0.0)
            if now_ts - last < float(interval):
                continue
            self._schedule_last[key] = now_ts
            out.append(
                WorkIntent(
                    kind="run_flow",
                    target=spec.work_flow_id,
                    payload={"trigger": "schedule"},
                    coalesce_key=spec.coalesce_key,
                )
            )
        return out

    def _match(
        self, spec: TriggerSpec, event_type: str, payload: dict[str, Any]
    ) -> WorkIntent | None:
        if spec.kind == "on_resource":
            if event_type != "resource.changed":
                return None
            ref = str(payload.get("resource_ref") or "")
            action = str(payload.get("action") or "").lower()
            if ref != (spec.resource or ""):
                return None
            if spec.actions and action not in spec.actions:
                return None
            return WorkIntent(
                kind="run_flow",
                target=spec.work_flow_id,
                payload={
                    "trigger": "on_resource",
                    "resource_ref": ref,
                    "action": action,
                },
                coalesce_key=spec.coalesce_key,
            )

        if spec.kind == "on_flow":
            if event_type not in {
                "flow.session.succeeded",
                "wizard.commit.succeeded",
            }:
                # also accept when= suffix match
                if not event_type.endswith(spec.when):
                    return None
            flow_id = str(
                payload.get("flow_id") or payload.get("flow_name") or ""
            )
            if flow_id != (spec.source_flow or ""):
                return None
            if spec.when and spec.when not in event_type and event_type not in {
                "flow.session.succeeded",
                "wizard.commit.succeeded",
            }:
                return None
            return WorkIntent(
                kind="run_flow",
                target=spec.work_flow_id,
                payload={"trigger": "on_flow", "source_flow": flow_id},
                coalesce_key=spec.coalesce_key,
            )

        return None


__all__ = ["TriggerRegistry"]
