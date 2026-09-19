"""Authoring kit — library walk over host.definitions (0.70.1).

One object holds :class:`~palm.services.definitions.service.DefinitionService`
and walks one-shot catalog commit.

Not an ``AuthoringService``. Not ``DesignService``. Not land verbs on
``palm.kits.present``. Handle class name stays unnamed (VISION-0.70 §9).

Library door: ``land(host)``. Job leaf: ``bound()`` from the started host.
``commit(body)`` walks catalog ``kind`` (``flow`` / ``resource``). José
locked the package ``palm.kits.authoring`` (2026-09-19). Constructor
spelling is as-built for the floor; rename is José's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.providers._registry import get_bound_runtime
from palm.kits.registry import register_kit

if TYPE_CHECKING:
    from palm.services.definitions.service import DefinitionService

register_kit(
    "authoring",
    description="Embedded library walk: one-shot commit on host.definitions",
    module="palm.kits.authoring",
)


def _land_flow(definitions: Any, body: dict[str, Any]) -> dict[str, Any]:
    return definitions.create_flow(body)


def _land_resource(definitions: Any, body: dict[str, Any]) -> dict[str, Any]:
    return definitions.create_resource(body)


_LAND = {
    "flow": _land_flow,
    "resource": _land_resource,
}


class _Authoring:
    """Holds DefinitionService and walks catalog create."""

    def __init__(self, *, definitions: DefinitionService) -> None:
        self._definitions = definitions

    def commit(self, body: dict[str, Any]) -> dict[str, Any]:
        kind = str((body or {}).get("kind") or "flow").strip()
        hand = _LAND.get(kind)
        if hand is None:
            raise ValueError(f"authoring commit does not land kind {kind!r}")
        return hand(self._definitions, body)


def land(host: Any) -> _Authoring:
    """Open an authoring walk on ``host.definitions``."""
    return _Authoring(definitions=host.definitions)


def bound() -> _Authoring:
    """Return the adapter for the started host on the bound runtime.

    Jobs have no host. Host start already binds the runtime (same door
    file/kv use). ``land(host)`` is the library door, not a kit-global stash.
    """
    runtime = get_bound_runtime()
    if runtime is None or not runtime.is_started:
        raise RuntimeError("authoring has no bound definitions; start the host first")
    host = runtime.application_host
    if host is None or host.definitions is None:
        raise RuntimeError("authoring has no bound definitions; start the host first")
    return _Authoring(definitions=host.definitions)


__all__ = ["land"]
