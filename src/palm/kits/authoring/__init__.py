"""Authoring kit — library walk over host.definitions (0.70.1).

One object holds :class:`~palm.services.definitions.service.DefinitionService`
and walks one-shot catalog commit.

Not an ``AuthoringService``. Not ``DesignService``. Not land verbs on
``palm.kits.present``. Handle class name stays unnamed (VISION-0.70 §9).

Library door: ``land(host)``. José locked the package ``palm.kits.authoring``
(2026-09-19). Constructor spelling is as-built for the floor; rename is José's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.kits.registry import register_kit

if TYPE_CHECKING:
    from palm.services.definitions.service import DefinitionService

register_kit(
    "authoring",
    description="Embedded library walk: one-shot commit on host.definitions",
    module="palm.kits.authoring",
)


_bound_definitions: DefinitionService | None = None


class _Authoring:
    """Holds DefinitionService and walks catalog create."""

    def __init__(self, *, definitions: DefinitionService) -> None:
        self._definitions = definitions

    def commit(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._definitions.create_flow(body)


def land(host: Any) -> _Authoring:
    """Open an authoring walk on ``host.definitions``."""
    global _bound_definitions
    _bound_definitions = host.definitions
    return _Authoring(definitions=host.definitions)


def bound() -> _Authoring:
    """Return the adapter bound by the last ``land(host)`` in this process.

    Named residual (SD-025): process-global bind. Jobs have no host.
    """
    if _bound_definitions is None:
        raise RuntimeError("authoring has no bound definitions; call land(host) first")
    return _Authoring(definitions=_bound_definitions)


__all__ = ["land"]
