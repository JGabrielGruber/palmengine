"""
Coconut NPC example pack — branching wizard + KV player persistence.

Registration order: **resources first**, then flow/process (resource_ref by name).

::

    palm flow start coconut-npc
"""

from __future__ import annotations

from . import npc, profile_pipeline, resources

__all__ = [
    "npc",
    "profile_pipeline",
    "resources",
    "register_definitions",
]


def register_definitions(repository: object) -> None:
    """Register coconut resources, then the npc flow/process."""
    resources.register_definitions(repository)
    profile_pipeline.register_definitions(repository)
    npc.register_definitions(repository)
