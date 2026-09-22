"""DAG pattern configuration — resource nodes with dependencies (0.54.3 v0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DagNodeSpec:
    """One DAG node: resource invoke **or** workload Spec (0.56)."""

    id: str
    resource_ref: str | None = None
    provider: str | None = None
    action: str | None = None
    resource_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    #: WorkloadSpec mapping (or run-python sugar). Exclusive of resource_ref/provider.
    workload: dict[str, Any] | None = None
    output_key: str | None = None
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not str(self.id).strip():
            raise ValueError("DAG node id must be non-empty")
        has_resource = bool(self.resource_ref or self.provider)
        has_workload = bool(self.workload)
        if has_resource and has_workload:
            raise ValueError(
                f"DAG node {self.id!r} cannot set both resource and workload"
            )
        if not has_resource and not has_workload:
            raise ValueError(
                f"DAG node {self.id!r} requires resource_ref/provider or workload"
            )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> DagNodeSpec:
        node_id = str(data.get("id") or data.get("name") or data.get("slug") or "").strip()
        deps_raw = data.get("depends_on") or data.get("deps") or []
        if isinstance(deps_raw, str):
            deps = (deps_raw,) if deps_raw.strip() else ()
        elif isinstance(deps_raw, list | tuple):
            deps = tuple(str(d).strip() for d in deps_raw if str(d).strip())
        else:
            raise ValueError(f"DAG node {node_id!r}: depends_on must be a list of ids")
        params = data.get("params")
        if params is not None and not isinstance(params, dict):
            raise ValueError(f"DAG node {node_id!r}: params must be a dict")
        workload = data.get("workload")
        if workload is not None and not isinstance(workload, dict):
            raise ValueError(f"DAG node {node_id!r}: workload must be a dict (Spec)")
        return cls(
            id=node_id,
            resource_ref=str(data["resource_ref"]) if data.get("resource_ref") else None,
            provider=str(data["provider"]) if data.get("provider") else None,
            action=str(data["action"]) if data.get("action") else None,
            resource_id=str(data["resource_id"]) if data.get("resource_id") else None,
            params=dict(params or {}),
            workload=dict(workload) if isinstance(workload, dict) else None,
            output_key=str(data["output_key"]) if data.get("output_key") else None,
            depends_on=deps,
        )


@dataclass(frozen=True)
class DagConfig:
    """Ordered DAG of resource nodes (topologically sorted at parse time)."""

    nodes: tuple[DagNodeSpec, ...]
    initial_state: dict[str, Any] = field(default_factory=dict)
    #: If True (default), nodes with empty depends_on are chained in list order.
    chain_implicit: bool = True
    #: If True (default, 0.54.8), run all currently ready nodes in one tick
    #: (sequential invokes). If False, run only the first ready node per tick.
    drain_ready: bool = True

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> DagConfig:
        nodes_raw = options.get("nodes") or options.get("steps")
        if not isinstance(nodes_raw, list) or not nodes_raw:
            raise ValueError("DAG requires a non-empty 'nodes' list (or 'steps' alias)")
        nodes = tuple(
            DagNodeSpec.from_mapping(item) for item in nodes_raw if isinstance(item, dict)
        )
        if not nodes:
            raise ValueError("DAG 'nodes' must contain node dicts")
        chain = bool(options.get("chain_implicit", True))
        if chain:
            nodes = _apply_implicit_chain(nodes)
        ordered = topological_sort(nodes)
        initial = options.get("initial_state")
        if initial is not None and not isinstance(initial, dict):
            raise ValueError("DAG initial_state must be a dict")
        drain = bool(options.get("drain_ready", True))
        return cls(
            nodes=ordered,
            initial_state=dict(initial or {}),
            chain_implicit=chain,
            drain_ready=drain,
        )


def _apply_implicit_chain(nodes: tuple[DagNodeSpec, ...]) -> tuple[DagNodeSpec, ...]:
    """If every node has empty depends_on, chain list order as linear deps."""
    if not nodes:
        return nodes
    if any(n.depends_on for n in nodes):
        return nodes
    out: list[DagNodeSpec] = []
    prev: str | None = None
    for n in nodes:
        deps = (prev,) if prev is not None else ()
        out.append(
            DagNodeSpec(
                id=n.id,
                resource_ref=n.resource_ref,
                provider=n.provider,
                action=n.action,
                resource_id=n.resource_id,
                params=dict(n.params),
                workload=dict(n.workload) if n.workload else None,
                output_key=n.output_key,
                depends_on=deps,
            )
        )
        prev = n.id
    return tuple(out)


def topological_sort(nodes: tuple[DagNodeSpec, ...]) -> tuple[DagNodeSpec, ...]:
    """Kahn topo-sort; raise on unknown deps or cycles."""
    by_id = {n.id: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("DAG node ids must be unique")
    for n in nodes:
        for d in n.depends_on:
            if d not in by_id:
                raise ValueError(f"DAG node {n.id!r} depends on unknown id {d!r}")

    indegree = {n.id: 0 for n in nodes}
    children: dict[str, list[str]] = {n.id: [] for n in nodes}
    for n in nodes:
        for d in n.depends_on:
            indegree[n.id] += 1
            children[d].append(n.id)

    queue = [nid for nid, deg in indegree.items() if deg == 0]
    # stable: preserve original relative order among ready nodes
    order_index = {n.id: i for i, n in enumerate(nodes)}
    queue.sort(key=lambda nid: order_index[nid])
    ordered: list[str] = []
    while queue:
        queue.sort(key=lambda nid: order_index[nid])
        nid = queue.pop(0)
        ordered.append(nid)
        for c in children[nid]:
            indegree[c] -= 1
            if indegree[c] == 0:
                queue.append(c)
    if len(ordered) != len(nodes):
        raise ValueError("DAG has a cycle among nodes")
    return tuple(by_id[nid] for nid in ordered)


__all__ = ["DagConfig", "DagNodeSpec", "topological_sort"]
