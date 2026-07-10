"""Parse ``ResourceDefinition.metadata.analytics`` exposure (0.35–0.36)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AnalyticsKind = Literal["fact", "view"]
AnalyticsPresentProfileName = Literal["raw", "table", "series", "kpi"]

_KNOWN_KEYS = frozenset(
    {
        "published",
        "kind",
        "derived_from",
        "default_profile",
        "row_path",
        "refresh",
        "virtual_steps",
        "source",
        "transform",
        "materialize",
        "fields",
    }
)
_KINDS = frozenset({"fact", "view"})
_PROFILES = frozenset({"raw", "table", "series", "kpi"})


@dataclass(frozen=True, slots=True)
class AnalyticsExposure:
    """Normalized BI exposure contract for a resource definition."""

    published: bool = False
    kind: AnalyticsKind = "fact"
    derived_from: tuple[str, ...] = ()
    default_profile: AnalyticsPresentProfileName = "table"
    row_path: str | None = None
    refresh: dict[str, Any] = field(default_factory=dict)
    virtual_steps: tuple[Any, ...] = ()
    source: str | None = None
    transform: dict[str, Any] = field(default_factory=dict)
    materialize: bool = True
    fields: tuple[dict[str, Any], ...] = ()
    unknown_keys: tuple[str, ...] = ()

    @property
    def is_virtual(self) -> bool:
        """True when query should load ``source`` and apply ``transform``."""
        return bool(self.source) and not self.materialize and bool(self.transform)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "published": self.published,
            "kind": self.kind,
            "derived_from": list(self.derived_from),
            "default_profile": self.default_profile,
            "materialize": self.materialize,
        }
        if self.row_path:
            out["row_path"] = self.row_path
        if self.refresh:
            out["refresh"] = dict(self.refresh)
        if self.virtual_steps:
            out["virtual_steps"] = list(self.virtual_steps)
        if self.source:
            out["source"] = self.source
        if self.transform:
            out["transform"] = dict(self.transform)
        if self.fields:
            out["fields"] = [dict(f) for f in self.fields]
        if self.unknown_keys:
            out["unknown_keys"] = list(self.unknown_keys)
        return out


def parse_analytics_exposure(
    metadata: dict[str, Any] | None,
    *,
    strict: bool = False,
) -> AnalyticsExposure:
    if not isinstance(metadata, dict):
        return AnalyticsExposure()
    raw = metadata.get("analytics")
    if raw is None:
        return AnalyticsExposure()
    if not isinstance(raw, dict):
        if strict:
            raise ValueError("metadata.analytics must be an object")
        return AnalyticsExposure()

    unknown = tuple(sorted(k for k in raw if k not in _KNOWN_KEYS))
    published = _bool(raw.get("published"), default=False, field="published", strict=strict)
    kind = _kind(raw.get("kind"), strict=strict)
    derived = _str_list(raw.get("derived_from"), field="derived_from", strict=strict)
    profile = _profile(raw.get("default_profile"), strict=strict)
    row_path = _optional_str(raw.get("row_path"), field="row_path", strict=strict)
    refresh = _dict(raw.get("refresh"), field="refresh", strict=strict)
    steps = _any_list(raw.get("virtual_steps"), field="virtual_steps", strict=strict)
    source = _optional_str(raw.get("source"), field="source", strict=strict)
    transform = _dict(raw.get("transform"), field="transform", strict=strict)
    fields = _field_entries(raw.get("fields"), strict=strict)

    if "materialize" in raw:
        materialize = _bool(
            raw.get("materialize"), default=True, field="materialize", strict=strict
        )
    else:
        # Virtual by default when source is set; otherwise materialize (legacy).
        materialize = source is None

    return AnalyticsExposure(
        published=published,
        kind=kind,
        derived_from=derived,
        default_profile=profile,
        row_path=row_path,
        refresh=refresh,
        virtual_steps=steps,
        source=source,
        transform=transform,
        materialize=materialize,
        fields=fields,
        unknown_keys=unknown,
    )


def is_analytics_published(metadata: dict[str, Any] | None) -> bool:
    return parse_analytics_exposure(metadata).published


def _bool(value: Any, *, default: bool, field: str, strict: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if strict:
        raise ValueError(f"analytics.{field} must be a boolean")
    return default


def _kind(value: Any, *, strict: bool) -> AnalyticsKind:
    if value is None:
        return "fact"
    if isinstance(value, str) and value in _KINDS:
        return value  # type: ignore[return-value]
    if strict:
        raise ValueError("analytics.kind must be 'fact' or 'view'")
    return "fact"


def _profile(value: Any, *, strict: bool) -> AnalyticsPresentProfileName:
    if value is None:
        return "table"
    if isinstance(value, str) and value in _PROFILES:
        return value  # type: ignore[return-value]
    if strict:
        raise ValueError("analytics.default_profile must be raw|table|series|kpi")
    return "table"


def _optional_str(value: Any, *, field: str, strict: bool) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    if strict:
        raise ValueError(f"analytics.{field} must be a string")
    return None


def _str_list(value: Any, *, field: str, strict: bool) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        if strict:
            raise ValueError(f"analytics.{field} must be a list of strings")
        return ()
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            out.append(item)
        elif strict:
            raise ValueError(f"analytics.{field} items must be non-empty strings")
    return tuple(out)


def _dict(value: Any, *, field: str, strict: bool) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if strict:
        raise ValueError(f"analytics.{field} must be an object")
    return {}


def _any_list(value: Any, *, field: str, strict: bool) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(value)
    if strict:
        raise ValueError(f"analytics.{field} must be a list")
    return ()


def _field_entries(value: Any, *, strict: bool) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        if strict:
            raise ValueError("analytics.fields must be a list")
        return ()
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict) and item.get("name"):
            out.append(dict(item))
        elif strict:
            raise ValueError("analytics.fields entries must be objects with name")
    return tuple(out)


__all__ = [
    "AnalyticsExposure",
    "AnalyticsKind",
    "AnalyticsPresentProfileName",
    "is_analytics_published",
    "parse_analytics_exposure",
]
