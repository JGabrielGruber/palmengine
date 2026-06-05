"""
Basic DAG primitives for future non-interactive workflows.

For the initial skeleton these are mostly placeholders that the
WizardEngine can evolve into or coexist with.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    id: str
    func: Callable[[dict[str, Any]], Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DAG:
    """Very small DAG container."""

    name: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, src: str, dst: str) -> None:
        if src not in self.nodes or dst not in self.nodes:
            raise ValueError("Both nodes must exist before adding edge")
        self.edges.append((src, dst))

    def topological(self) -> list[str]:
        from palm.utils.graph import topological_sort

        return topological_sort(list(self.nodes.keys()), self.edges)
