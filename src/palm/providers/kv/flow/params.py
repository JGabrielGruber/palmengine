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
        return cls(
            namespace=str(known.get("namespace") or "default"),
            backend=str(known.get("backend") or "auto"),
            default=known.get("default"),
            value=known.get("value"),
            prefix=str(known.get("prefix") or ""),
            extras=extras,
        )


_FIELD_NAMES = {item.name for item in fields(KvInvokeParams)}


__all__ = ["KvInvokeParams"]