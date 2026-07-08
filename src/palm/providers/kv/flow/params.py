"""Typed invoke parameters for the KV resource provider."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class KvInvokeParams:
    """Structured parameters for KV provider invocations."""

    namespace: str = "default"
    backend: str = "auto"
    default: Any = None
    value: Any = None
    prefix: str = ""
    hot_max_keys: int = 500
    cold_root: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, params: dict[str, Any] | None = None, **kwargs: Any) -> KvInvokeParams:
        merged = dict(params or {})
        merged.update(kwargs)
        known: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for key, value in merged.items():
            if key in _FIELD_NAMES:
                known[key] = value
            else:
                extras[key] = value
        hot_max_keys = known.get("hot_max_keys", 500)
        try:
            hot_max_keys = int(hot_max_keys)
        except (TypeError, ValueError):
            hot_max_keys = 500
        cold_root = known.get("cold_root")
        return cls(
            namespace=str(known.get("namespace") or "default"),
            backend=str(known.get("backend") or "auto"),
            default=known.get("default"),
            value=known.get("value"),
            prefix=str(known.get("prefix") or ""),
            hot_max_keys=max(1, hot_max_keys),
            cold_root=str(cold_root) if cold_root is not None else None,
            extras=extras,
        )


_FIELD_NAMES = {item.name for item in fields(KvInvokeParams)}


__all__ = ["KvInvokeParams"]