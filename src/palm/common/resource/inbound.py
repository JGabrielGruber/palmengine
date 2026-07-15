"""Parse ``ResourceDefinition.metadata.inbound`` — resources can listen (0.43)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

InboundMode = Literal["webhook", "stream", "poll"]

_KNOWN_KEYS = frozenset(
    {
        "enabled",
        "mode",
        "path",
        "secret_header",
        "secret_param",
        "url",
        "work",
        "coalesce_key",
        "coalesce_field",
        "debounce_seconds",
        "store_action",
        "store_resource",
        "event_types",
    }
)
_MODES = frozenset({"webhook", "stream", "poll"})


@dataclass(frozen=True, slots=True)
class InboundWork:
    """WorkIntent target when an inbound signal arrives."""

    kind: str = "run_flow"
    flow_id: str = ""
    process_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind}
        if self.flow_id:
            out["flow_id"] = self.flow_id
        if self.process_id:
            out["process_id"] = self.process_id
        return out

    @property
    def target(self) -> str:
        if self.kind == "run_process":
            return self.process_id
        return self.flow_id


@dataclass(frozen=True, slots=True)
class InboundSpec:
    """Normalized inbound contract for a resource definition."""

    enabled: bool = False
    mode: InboundMode = "webhook"
    path: str | None = None
    secret_header: str | None = None
    secret_param: str | None = None
    url: str | None = None
    work: InboundWork = field(default_factory=InboundWork)
    coalesce_key: str | None = None
    coalesce_field: str | None = None
    debounce_seconds: float = 0.0
    store_action: str | None = None
    store_resource: str | None = None
    event_types: tuple[str, ...] = ()
    unknown_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "enabled": self.enabled,
            "mode": self.mode,
            "work": self.work.to_dict(),
            "debounce_seconds": self.debounce_seconds,
        }
        if self.path:
            out["path"] = self.path
        if self.secret_header:
            out["secret_header"] = self.secret_header
        if self.secret_param:
            out["secret_param"] = self.secret_param
        if self.url:
            out["url"] = self.url
        if self.coalesce_key:
            out["coalesce_key"] = self.coalesce_key
        if self.coalesce_field:
            out["coalesce_field"] = self.coalesce_field
        if self.store_action:
            out["store_action"] = self.store_action
        if self.store_resource:
            out["store_resource"] = self.store_resource
        if self.event_types:
            out["event_types"] = list(self.event_types)
        if self.unknown_keys:
            out["unknown_keys"] = list(self.unknown_keys)
        return out


def parse_inbound_spec(
    metadata: dict[str, Any] | None,
    *,
    strict: bool = False,
) -> InboundSpec | None:
    """Return :class:`InboundSpec` when ``metadata.inbound`` is present; else None."""
    if not isinstance(metadata, dict):
        return None
    raw = metadata.get("inbound")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        if strict:
            raise ValueError("metadata.inbound must be an object")
        return None

    unknown = tuple(sorted(k for k in raw if k not in _KNOWN_KEYS))
    enabled = _bool(raw.get("enabled"), default=True, field="enabled", strict=strict)
    mode = _mode(raw.get("mode"), strict=strict)
    path = _optional_str(raw.get("path"), field="path", strict=strict)
    secret_header = _optional_str(
        raw.get("secret_header"), field="secret_header", strict=strict
    )
    secret_param = _optional_str(
        raw.get("secret_param"), field="secret_param", strict=strict
    )
    url = _optional_str(raw.get("url"), field="url", strict=strict)
    work = _work(raw.get("work"), strict=strict)
    coalesce_key = _optional_str(
        raw.get("coalesce_key"), field="coalesce_key", strict=strict
    )
    coalesce_field = _optional_str(
        raw.get("coalesce_field"), field="coalesce_field", strict=strict
    )
    debounce = _float(
        raw.get("debounce_seconds"), default=0.0, field="debounce_seconds", strict=strict
    )
    store_action = _optional_str(
        raw.get("store_action"), field="store_action", strict=strict
    )
    store_resource = _optional_str(
        raw.get("store_resource"), field="store_resource", strict=strict
    )
    event_types = _str_tuple(raw.get("event_types"), field="event_types", strict=strict)

    if enabled and not work.target:
        if strict:
            raise ValueError("metadata.inbound.work requires flow_id or process_id")
        # keep enabled=False so host does not bind a no-op
        enabled = False

    return InboundSpec(
        enabled=enabled,
        mode=mode,
        path=path,
        secret_header=secret_header,
        secret_param=secret_param,
        url=url,
        work=work,
        coalesce_key=coalesce_key,
        coalesce_field=coalesce_field,
        debounce_seconds=debounce,
        store_action=store_action,
        store_resource=store_resource,
        event_types=event_types,
        unknown_keys=unknown,
    )


def is_inbound_enabled(metadata: dict[str, Any] | None) -> bool:
    spec = parse_inbound_spec(metadata)
    return bool(spec and spec.enabled and spec.work.target)


def _work(raw: Any, *, strict: bool) -> InboundWork:
    if raw is None:
        return InboundWork()
    if not isinstance(raw, dict):
        if strict:
            raise ValueError("metadata.inbound.work must be an object")
        return InboundWork()
    kind = str(raw.get("kind") or "run_flow").strip() or "run_flow"
    flow_id = str(raw.get("flow_id") or raw.get("target") or "").strip()
    process_id = str(raw.get("process_id") or "").strip()
    if kind == "run_process" and not process_id and flow_id:
        process_id = flow_id
        flow_id = ""
    return InboundWork(kind=kind, flow_id=flow_id, process_id=process_id)


def _mode(raw: Any, *, strict: bool) -> InboundMode:
    if raw is None:
        return "webhook"
    s = str(raw).strip().lower()
    if s in _MODES:
        return s  # type: ignore[return-value]
    if strict:
        raise ValueError(f"metadata.inbound.mode must be one of {sorted(_MODES)}")
    return "webhook"


def _bool(raw: Any, *, default: bool, field: str, strict: bool) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)) and raw in (0, 1):
        return bool(raw)
    if isinstance(raw, str):
        low = raw.strip().lower()
        if low in ("true", "1", "yes", "on"):
            return True
        if low in ("false", "0", "no", "off"):
            return False
    if strict:
        raise ValueError(f"metadata.inbound.{field} must be a boolean")
    return default


def _optional_str(raw: Any, *, field: str, strict: bool) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        return s or None
    if strict:
        raise ValueError(f"metadata.inbound.{field} must be a string")
    return str(raw).strip() or None


def _float(raw: Any, *, default: float, field: str, strict: bool) -> float:
    if raw is None:
        return default
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        if strict:
            raise ValueError(f"metadata.inbound.{field} must be a number") from None
        return default


def _str_tuple(raw: Any, *, field: str, strict: bool) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return tuple(parts)
    if isinstance(raw, (list, tuple)):
        out: list[str] = []
        for item in raw:
            s = str(item).strip()
            if s:
                out.append(s)
        return tuple(out)
    if strict:
        raise ValueError(f"metadata.inbound.{field} must be a list or string")
    return ()


__all__ = [
    "InboundMode",
    "InboundSpec",
    "InboundWork",
    "is_inbound_enabled",
    "parse_inbound_spec",
]
