"""
Lightweight graph utilities for DAG validation and traversal.

Used by workflow and wizard engines for step ordering and path analysis.
"""

from __future__ import annotations

from collections import defaultdict, deque


def topological_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """
    Return nodes in topological order.

    edges are (from, to) pairs meaning "from" precedes "to".
    Raises ValueError on cycles.
    """
    graph: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {n: 0 for n in nodes}

    for src, dst in edges:
        graph[src].append(dst)
        indegree[dst] = indegree.get(dst, 0) + 1
        if src not in indegree:
            indegree[src] = 0

    queue = deque([n for n, d in indegree.items() if d == 0])
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(indegree):
        raise ValueError("Cycle detected in graph")
    return result


def find_path(
    start: str,
    end: str,
    edges: list[tuple[str, str]],
) -> list[str] | None:
    """Simple BFS path reconstruction. Returns None if no path."""
    graph: dict[str, list[str]] = defaultdict(list)
    for src, dst in edges:
        graph[src].append(dst)

    parent: dict[str, str | None] = {start: None}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        if current == end:
            break
        for neighbor in graph[current]:
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)

    if end not in parent:
        return None

    # Reconstruct
    path: list[str] = []
    node: str | None = end
    while node is not None:
        path.append(node)
        node = parent[node]
    return list(reversed(path))
