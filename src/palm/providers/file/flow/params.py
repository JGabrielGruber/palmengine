"""Typed invoke parameters for the file document resource provider."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class FileInvokeParams:
    """Structured parameters for file provider invocations."""

    documents_root: str | None = None
    format: str = "json"
    content: Any = None
    value: Any = None
    glob: str = "**/*"
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, params: dict[str, Any] | None = None, **kwargs: Any) -> FileInvokeParams:
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
            documents_root=known.get("documents_root"),
            format=str(known.get("format") or "json"),
            content=known.get("content"),
            value=known.get("value"),
            glob=str(known.get("glob") or "**/*"),
            extras=extras,
        )

    @property
    def write_payload(self) -> Any | None:
        if self.content is not None:
            return self.content
        return self.value


_FIELD_NAMES = {item.name for item in fields(FileInvokeParams)}


__all__ = ["FileInvokeParams"]