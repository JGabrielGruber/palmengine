"""Choices a minimal application supplies. Plugins stay on this record."""

from __future__ import annotations

from dataclasses import dataclass

from bundles.minimal.bootstrap import MEMORY_STORAGE


@dataclass(frozen=True)
class MinimalDefinition:
    """Storage plugin, other plugin modules, and the structure definition id."""

    storage_backend: str
    modules: tuple[str, ...]
    structure_definition_id: str

    def __post_init__(self) -> None:
        if not self.storage_backend.strip():
            raise ValueError("storage_backend is empty")
        if not self.structure_definition_id.strip():
            raise ValueError("structure_definition_id is empty")
        if any(not module.strip() for module in self.modules):
            raise ValueError("plugin module name is empty")


DEFAULT_DEFINITION = MinimalDefinition(
    storage_backend="memory",
    modules=(MEMORY_STORAGE,),
    structure_definition_id="local.embedded",
)
