"""Palm-backed todo store for the mobile MVP.

ApplicationHost + memory kv (put-palm-todos / palm-todos) is the engine of
truth. Thin ops (list / add / toggle) sit above invoke_resource so Flutter
can drive a list UI without walking the collection-wizard UX.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

# Palm
from palm.core import StorageEngine
from palm.definitions import FlowDefinition, ResourceDefinition

import plugins.patterns  # noqa: F401
import plugins.providers  # noqa: F401
import plugins.storages.memory  # noqa: F401

from bundles.standard.app import ApplicationHost, DeploymentProfile, PalmSettings
from bundles.standard.app.bootstrap import runtime_start_options



PUT_TODOS = ResourceDefinition(
    id="resource-put-palm-todos",
    name="put-palm-todos",
    provider="kv",
    action="put",
    resource_id="todos/list",
    params={
        "namespace": "palm",
        "backend": "auto",
        "value": "{{ state.todos }}",
    },
    metadata={"tags": ["palm", "todo", "kv", "write"]},
)

GET_TODOS = ResourceDefinition(
    id="resource-palm-todos",
    name="palm-todos",
    provider="kv",
    action="get",
    resource_id="todos/list",
    params={
        "namespace": "palm",
        "backend": "auto",
        "default": [],
    },
    metadata={"tags": ["palm", "todo", "kv", "read"]},
)

# Thin persist flow — state.todos → put-palm-todos (no interactive steps).
TODO_PERSIST_FLOW = FlowDefinition(
    id="flow-todo-persist",
    name="todo-persist",
    pattern="wizard",
    state_schema={
        "type": "object",
        "properties": {
            "todos": {"type": "array"},
        },
        "required": ["todos"],
    },
    options={
        "include_summary": False,
        "include_commit": False,
        "steps": [
            {
                "slug": "save_todos",
                "title": "Save todos",
                "prompt": "Persist list to kv (put-palm-todos)",
                "step_kind": "resource",
                "resource_ref": "put-palm-todos",
            },
        ],
    },
)


@dataclass
class TodoItem:
    id: str
    title: str
    done: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "done": self.done}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TodoItem:
        return cls(
            id=str(data.get("id") or ""),
            title=str(data.get("title") or ""),
            done=bool(data.get("done", False)),
        )


class TodoEngine:
    """Owns ApplicationHost and exposes list/add/toggle over Palm kv."""

    def __init__(self) -> None:
        self._host: ApplicationHost | None = None

    @property
    def host(self) -> ApplicationHost:
        if self._host is None:
            raise RuntimeError("TodoEngine not started")
        return self._host

    def start(self) -> None:
        storage = StorageEngine()
        storage.initialize(backend="memory")
        settings = PalmSettings(load_example_definitions=False)
        host = ApplicationHost(
            settings,
            profile=DeploymentProfile.all_in_one(),
            storage=storage,
        )
        host.start(**runtime_start_options(settings))
        repo = host.app.runtime().repository
        repo.save_resource(PUT_TODOS)
        repo.save_resource(GET_TODOS)
        repo.save_flow(TODO_PERSIST_FLOW)
        # Seed empty list via Palm resource path.
        host.invoke_resource("put-palm-todos", params={"value": []})
        self._host = host

    def shutdown(self) -> None:
        if self._host is not None:
            self._host.shutdown()
            self._host = None

    def list_todos(self) -> list[TodoItem]:
        result = self.host.invoke_resource("palm-todos")
        if not result.success:
            raise RuntimeError(result.error or "palm-todos get failed")
        raw = (result.data or {}).get("value") or []
        if not isinstance(raw, list):
            return []
        return [TodoItem.from_dict(x) for x in raw if isinstance(x, dict)]

    def _persist(self, items: list[TodoItem]) -> None:
        payload = [t.to_dict() for t in items]
        # Prefer the registered flow so Palm orchestration is on the path.
        job = self.host.submit_flow("todo-persist", state={"todos": payload})
        # Resource-only wizard should finish synchronously under EmbeddedRuntime.
        from palm.core.orchestration import JobStatus

        if job.status != JobStatus.SUCCEEDED:
            # Fallback: direct put if flow waiting (defensive).
            result = self.host.invoke_resource(
                "put-palm-todos", params={"value": payload}
            )
            if not result.success:
                raise RuntimeError(
                    f"persist failed: flow={job.status} put={result.error}"
                )

    def add_todo(self, title: str) -> TodoItem:
        cleaned = (title or "").strip()
        if not cleaned:
            raise ValueError("title required")
        items = self.list_todos()
        item = TodoItem(id=str(uuid.uuid4()), title=cleaned, done=False)
        items.append(item)
        self._persist(items)
        return item

    def toggle_todo(self, todo_id: str, done: bool) -> TodoItem:
        items = self.list_todos()
        found: TodoItem | None = None
        for item in items:
            if item.id == todo_id:
                item.done = bool(done)
                found = item
                break
        if found is None:
            raise KeyError(f"todo not found: {todo_id}")
        self._persist(items)
        return found

    def handle_op(self, msg: dict[str, Any]) -> dict[str, Any]:
        """JSON/RPC dispatcher matching ui-spec intents."""
        op = msg.get("op")
        try:
            if op == "list":
                items = [t.to_dict() for t in self.list_todos()]
                return {"op": "list_result", "items": items}
            if op == "add":
                item = self.add_todo(str(msg.get("title") or ""))
                return {"op": "todo_added", "item": item.to_dict()}
            if op == "toggle":
                item = self.toggle_todo(
                    str(msg.get("id") or ""), bool(msg.get("done", True))
                )
                return {
                    "op": "todo_toggled",
                    "id": item.id,
                    "done": item.done,
                }
            if op == "ping":
                return {"op": "pong"}
            return {"op": "list_error", "message": f"unknown op: {op}"}
        except Exception as exc:  # noqa: BLE001 — surface to Flutter
            return {"op": "list_error", "message": str(exc)}


__all__ = ["TodoEngine", "TodoItem", "PUT_TODOS", "GET_TODOS", "TODO_PERSIST_FLOW"]
