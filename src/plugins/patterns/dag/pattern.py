"""
DAG pattern — execute resource **or workload** nodes with dependencies.

v0: one ready node / drain_ready batch per tick. Resource nodes use
ResourceInvoker; workload nodes use WorkloadDriver (0.56 / 0.57.4). State under ``dag.*``.
"""

from __future__ import annotations

from typing import Any

from palm.system.subsystems.planes.workload.run_python import spec_from_bound_params
from palm.core.behavior_tree import BasePattern, PatternStatus
from palm.core.context import BaseState
from palm.core.resource.invocation import bind_resource_params
from palm.core.resource.invoker import ResourceInvoker
from palm.core.resource.observability import resource_correlation
from palm.core.workload import WorkloadDriver, WorkloadOwner, WorkloadStatus
from plugins.patterns.dag.bindings.definitions.config import DagConfig, DagNodeSpec

_DAG_KEY = "dag"
_STATUS_PENDING = "pending"
_STATUS_SUCCEEDED = "succeeded"
_STATUS_FAILED = "failed"


class DagPattern(BasePattern):
    """Run a DAG of resource/workload steps; linear or explicit depends_on."""

    def __init__(
        self,
        *,
        name: str = "dag",
        config: DagConfig | None = None,
        resource_engine: ResourceInvoker | None = None,
        workload_engine: WorkloadDriver | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            raise ValueError("DagPattern requires a DagConfig")
        self._config = config
        self._resource_engine = resource_engine
        self._workload_engine = workload_engine
        self._seeded = False

    @property
    def config(self) -> DagConfig:
        return self._config

    def tick(self, state: BaseState) -> PatternStatus:
        self._seed_initial_state(state)
        dag = self._ensure_dag_state(state)

        if dag.get("status") == _STATUS_SUCCEEDED:
            return PatternStatus.SUCCESS
        if dag.get("status") == _STATUS_FAILED:
            return PatternStatus.FAILURE

        # 0.54.8: drain ready-set (and newly unlocked nodes) in one tick when
        # drain_ready; otherwise a single ready node per tick.
        last = PatternStatus.RUNNING
        while True:
            dag = state.get(_DAG_KEY)
            if not isinstance(dag, dict):
                return PatternStatus.FAILURE
            if dag.get("status") == _STATUS_FAILED:
                return PatternStatus.FAILURE
            if dag.get("status") == _STATUS_SUCCEEDED:
                return PatternStatus.SUCCESS

            ready = self._ready_nodes(dag)
            if not ready:
                if self._all_succeeded(dag):
                    dag["status"] = _STATUS_SUCCEEDED
                    state.set(_DAG_KEY, dag)
                    return PatternStatus.SUCCESS
                dag["status"] = _STATUS_FAILED
                dag["error"] = "DAG stuck: no ready nodes and not all succeeded"
                state.set(_DAG_KEY, dag)
                return PatternStatus.FAILURE

            batch = list(ready) if self._config.drain_ready else ready[:1]
            for node in batch:
                dag = state.get(_DAG_KEY)
                if not isinstance(dag, dict) or dag.get("status") == _STATUS_FAILED:
                    return PatternStatus.FAILURE
                st = ((dag.get("nodes") or {}).get(node.id) or {}).get("status")
                if st != _STATUS_PENDING:
                    continue
                node_state = dag.get("nodes") or {}
                deps_ok = all(
                    (node_state.get(d) or {}).get("status") == _STATUS_SUCCEEDED
                    for d in node.depends_on
                )
                if not deps_ok:
                    continue
                last = self._run_node(state, dag, node)
                if last in (PatternStatus.FAILURE, PatternStatus.SUCCESS):
                    return last
            if not self._config.drain_ready:
                break
            # drain_ready: loop to pick up nodes unlocked by this batch (e.g. join)
        return last

    def reset(self) -> None:
        self._seeded = False

    def _seed_initial_state(self, state: BaseState) -> None:
        if self._seeded or not self._config.initial_state:
            return
        for key, value in self._config.initial_state.items():
            if not state.has(key):
                state.set(key, value)
        self._seeded = True

    def _ensure_dag_state(self, state: BaseState) -> dict[str, Any]:
        raw = state.get(_DAG_KEY)
        if isinstance(raw, dict) and raw.get("nodes"):
            return raw
        nodes_state = {
            n.id: {"status": _STATUS_PENDING, "output_key": n.output_key or n.id}
            for n in self._config.nodes
        }
        dag = {
            "status": "running",
            "order": [n.id for n in self._config.nodes],
            "nodes": nodes_state,
        }
        state.set(_DAG_KEY, dag)
        return dag

    def _ready_nodes(self, dag: dict[str, Any]) -> list[DagNodeSpec]:
        node_state = dag.get("nodes") or {}
        ready: list[DagNodeSpec] = []
        for n in self._config.nodes:
            st = (node_state.get(n.id) or {}).get("status")
            if st != _STATUS_PENDING:
                continue
            deps_ok = all(
                (node_state.get(d) or {}).get("status") == _STATUS_SUCCEEDED
                for d in n.depends_on
            )
            if deps_ok:
                ready.append(n)
        return ready

    def _all_succeeded(self, dag: dict[str, Any]) -> bool:
        node_state = dag.get("nodes") or {}
        return all(
            (node_state.get(n.id) or {}).get("status") == _STATUS_SUCCEEDED
            for n in self._config.nodes
        )

    def _run_node(
        self,
        state: BaseState,
        dag: dict[str, Any],
        node: DagNodeSpec,
    ) -> PatternStatus:
        nodes_state: dict[str, Any] = dict(dag.get("nodes") or {})
        entry = dict(nodes_state.get(node.id) or {})
        entry["status"] = "running"
        nodes_state[node.id] = entry
        dag["nodes"] = nodes_state
        dag["current"] = node.id
        state.set(_DAG_KEY, dag)

        output_key = node.output_key or node.id

        if node.workload is not None:
            return self._run_workload_node(state, dag, node, nodes_state, output_key)

        if self._resource_engine is None:
            return self._fail_node(state, dag, node, "ResourceInvoker is not configured")
        if not self._resource_engine.is_initialized:
            self._resource_engine.initialize()

        result = self._resource_engine.invoke(
            node.resource_ref,
            provider=node.provider,
            action=node.action,
            resource_id=node.resource_id,
            params=dict(node.params),
            state=state,
            correlation=resource_correlation(state, wizard=self.name, step_slug=node.id),
        )

        if result.success:
            state.set(output_key, result.data)
            return self._succeed_node(state, dag, node, nodes_state, output_key)

        err = result.error or "resource invoke failed"
        return self._fail_node(state, dag, node, err)

    def _run_workload_node(
        self,
        state: BaseState,
        dag: dict[str, Any],
        node: DagNodeSpec,
        nodes_state: dict[str, Any],
        output_key: str,
    ) -> PatternStatus:
        engine = self._workload_engine
        if engine is None:
            return self._fail_node(state, dag, node, "WorkloadDriver is not configured")
        if not engine.is_initialized:
            engine.initialize()
        try:
            bound = bind_resource_params(dict(node.workload or {}), state)
            # Merge node.params into workload if present (legacy style)
            if node.params:
                bound = {**bound, **bind_resource_params(dict(node.params), state)}
            # Default hermetic neonroot when isolation/runtime omitted
            if "kind" not in bound and "command" in bound:
                bound.setdefault("kind", "run")
                bound.setdefault("isolation", "hermetic")
                bound.setdefault("lifecycle", "job")
                placement = dict(bound.get("placement") or {})
                placement.setdefault("runtime", "neonroot")
                bound["placement"] = placement
            from palm.core.workload import WorkloadSpec

            if bound.get("kind"):
                spec = WorkloadSpec.from_dict(bound)
            else:
                spec = spec_from_bound_params(bound)
            wl = engine.start(spec, owner=WorkloadOwner(created_by_palm=True))
        except Exception as exc:
            return self._fail_node(state, dag, node, str(exc))

        payload = wl.to_dict()
        state.set(output_key, payload)
        if wl.status is WorkloadStatus.STOPPED and (
            wl.result is None or wl.result.success
        ):
            return self._succeed_node(state, dag, node, nodes_state, output_key)
        if wl.status is WorkloadStatus.FAILED or (
            wl.result is not None and not wl.result.success
        ):
            err = (
                (wl.result.error if wl.result else None)
                or wl.message
                or f"workload {wl.status}"
            )
            return self._fail_node(state, dag, node, str(err))
        # RUNNING/READY — treat as success for fire-and-forget workspace; fail closed for v0 runs
        return self._fail_node(
            state,
            dag,
            node,
            f"workload not terminal (status={wl.status}); async DAG wait later",
        )

    def _succeed_node(
        self,
        state: BaseState,
        dag: dict[str, Any],
        node: DagNodeSpec,
        nodes_state: dict[str, Any],
        output_key: str,
    ) -> PatternStatus:
        entry = dict(nodes_state.get(node.id) or {})
        entry["status"] = _STATUS_SUCCEEDED
        entry["output_key"] = output_key
        nodes_state[node.id] = entry
        dag["nodes"] = nodes_state
        if self._all_succeeded(dag):
            dag["status"] = _STATUS_SUCCEEDED
            dag.pop("current", None)
            state.set(_DAG_KEY, dag)
            return PatternStatus.SUCCESS
        state.set(_DAG_KEY, dag)
        return PatternStatus.RUNNING

    def _fail_node(
        self,
        state: BaseState,
        dag: dict[str, Any],
        node: DagNodeSpec,
        error: str,
    ) -> PatternStatus:
        nodes_state = dict(dag.get("nodes") or {})
        entry = dict(nodes_state.get(node.id) or {})
        entry["status"] = _STATUS_FAILED
        entry["error"] = error
        nodes_state[node.id] = entry
        dag["nodes"] = nodes_state
        dag["status"] = _STATUS_FAILED
        dag["error"] = f"node {node.id!r}: {error}"
        dag["current"] = node.id
        state.set(_DAG_KEY, dag)
        state.set(f"dag_error_{node.id}", error)
        return PatternStatus.FAILURE


__all__ = ["DagPattern"]
