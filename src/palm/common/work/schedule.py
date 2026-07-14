"""Durable schedule ticks → WorkIntent enqueue (0.41.1).

Next-fire times live on StorageEngine so restarts do not reset intervals.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine
    from palm.common.work.store import WorkIntentStore

SCHEDULE_PREFIX = "palm:schedule:entry:"
SCHEDULE_INDEX = "palm:schedule:index"


def _now() -> datetime:
    return datetime.now(UTC)


class ScheduleRegistry:
    """Interval schedules (``interval_seconds``). Cron syntax is 0.41+ later."""

    def __init__(
        self,
        storage: StorageEngine,
        work_store: WorkIntentStore,
    ) -> None:
        self._storage = storage
        self._work = work_store

    def upsert(
        self,
        schedule_id: str,
        *,
        flow_id: str,
        interval_seconds: float,
        enabled: bool = True,
        payload: dict[str, Any] | None = None,
        coalesce_key: str | None = None,
        preserve_next_fire: bool = True,
    ) -> dict[str, Any]:
        sid = str(schedule_id or "").strip()
        if not sid:
            raise ValueError("schedule_id required")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        existing = self._storage.get(f"{SCHEDULE_PREFIX}{sid}")
        next_fire = _now().isoformat()
        if (
            preserve_next_fire
            and isinstance(existing, dict)
            and existing.get("next_fire_at")
        ):
            next_fire = str(existing["next_fire_at"])
        entry = {
            "id": sid,
            "flow_id": str(flow_id),
            "interval_seconds": float(interval_seconds),
            "enabled": bool(enabled),
            "payload": dict(payload or {}),
            "coalesce_key": coalesce_key or f"schedule:{sid}",
            "next_fire_at": next_fire,
        }
        if isinstance(existing, dict) and existing.get("last_fire_at"):
            entry["last_fire_at"] = existing["last_fire_at"]
        self._storage.set(f"{SCHEDULE_PREFIX}{sid}", entry)
        index = self._load_index()
        if sid not in index:
            index.append(sid)
            self._storage.set(SCHEDULE_INDEX, index)
        return entry

    def remove(self, schedule_id: str) -> bool:
        sid = str(schedule_id or "").strip()
        had = self._storage.get(f"{SCHEDULE_PREFIX}{sid}") is not None
        self._storage.delete(f"{SCHEDULE_PREFIX}{sid}")
        index = [x for x in self._load_index() if x != sid]
        self._storage.set(SCHEDULE_INDEX, index)
        return had

    def list_entries(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for sid in self._load_index():
            raw = self._storage.get(f"{SCHEDULE_PREFIX}{sid}")
            if isinstance(raw, dict):
                out.append(raw)
        return out

    def tick(self, *, now: datetime | None = None, limit: int = 20) -> list[str]:
        """Fire due schedules: enqueue WorkIntent, advance next_fire_at."""
        now = now or _now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        fired: list[str] = []
        for sid in list(self._load_index()):
            if len(fired) >= limit:
                break
            raw = self._storage.get(f"{SCHEDULE_PREFIX}{sid}")
            if not isinstance(raw, dict) or not raw.get("enabled", True):
                continue
            next_s = str(raw.get("next_fire_at") or "")
            try:
                nxt = datetime.fromisoformat(next_s.replace("Z", "+00:00"))
                if nxt.tzinfo is None:
                    nxt = nxt.replace(tzinfo=UTC)
            except ValueError:
                nxt = now
            if nxt > now:
                continue
            interval = float(raw.get("interval_seconds") or 60)
            intent = WorkIntent(
                kind="run_flow",
                target=str(raw.get("flow_id") or ""),
                id=f"sched-{uuid4().hex[:12]}",
                payload={
                    "trigger": "schedule",
                    **dict(raw.get("payload") or {}),
                },
                coalesce_key=str(raw.get("coalesce_key") or f"schedule:{sid}"),
            )
            iid = self._work.enqueue(intent)
            raw = {
                **raw,
                "next_fire_at": (now + timedelta(seconds=interval)).isoformat(),
                "last_fire_at": now.isoformat(),
                "last_intent_id": iid,
            }
            self._storage.set(f"{SCHEDULE_PREFIX}{sid}", raw)
            fired.append(iid)
        return fired

    def sync_from_trigger_specs(
        self,
        specs: list[tuple[str, Any]],
    ) -> int:
        """Upsert schedule specs from TriggerRegistry (owner, TriggerSpec)."""
        n = 0
        for owner, spec in specs:
            if getattr(spec, "kind", None) != "schedule":
                continue
            interval = getattr(spec, "interval_seconds", None)
            if interval is None or float(interval) <= 0:
                continue
            flow_id = str(getattr(spec, "work_flow_id", None) or owner)
            sid = str(getattr(spec, "coalesce_key", None) or f"{owner}:schedule")
            self.upsert(
                sid,
                flow_id=flow_id,
                interval_seconds=float(interval),
                coalesce_key=str(
                    getattr(spec, "coalesce_key", None) or f"schedule:{sid}"
                ),
                preserve_next_fire=True,
            )
            n += 1
        return n

    def load_from_flow_rows(
        self,
        flow_rows: list[dict[str, Any]],
        *,
        get_metadata: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> int:
        from palm.common.triggers.parse import parse_triggers

        n = 0
        for row in flow_rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("flow_id") or "").strip()
            if not name:
                continue
            meta: dict[str, Any] | None = None
            if callable(get_metadata):
                try:
                    meta = get_metadata(name)
                except Exception:
                    meta = None
            if meta is None:
                meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else None
            if not isinstance(meta, dict):
                continue
            for i, spec in enumerate(parse_triggers(meta)):
                if spec.kind != "schedule":
                    continue
                if spec.interval_seconds is None or float(spec.interval_seconds) <= 0:
                    continue
                sid = spec.coalesce_key or f"{name}:schedule:{i}"
                self.upsert(
                    sid,
                    flow_id=spec.work_flow_id or name,
                    interval_seconds=float(spec.interval_seconds),
                    coalesce_key=spec.coalesce_key or f"schedule:{sid}",
                    preserve_next_fire=True,
                )
                n += 1
        return n

    def _load_index(self) -> list[str]:
        raw = self._storage.get(SCHEDULE_INDEX)
        if isinstance(raw, list):
            return [str(x) for x in raw if x]
        return []


__all__ = ["SCHEDULE_INDEX", "SCHEDULE_PREFIX", "ScheduleRegistry"]
