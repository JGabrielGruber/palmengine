"""Palm analytics dogfood — todos fact/view after materialize (and commit path)."""

from __future__ import annotations

from examples.definitions.todo_builder import register_definitions as register_todo_builder
from examples.definitions.todo_resources import (
    SEED_TODO_ROWS,
    materialize_todo_analytics,
)
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings


def test_todo_analytics_materialize_and_query() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=HostProfile.all_in_one(),
    ) as host:
        register_todo_builder(host.app.repository())
        result = materialize_todo_analytics(host.execution.providers)
        assert result["todo_rows"] == len(SEED_TODO_ROWS)
        assert result["fact_put"].get("success") is True
        assert result["view_put"].get("success") is True

        names = {r["dataset"] for r in host.analytics.list_datasets()}
        assert "palm-todos" in names
        assert "palm-todos-by-priority" in names
        assert "sales-facts-daily" not in names

        table = host.analytics.query(
            "palm-todos",
            profile="table",
            select=["title", "priority"],
        )
        assert table["status"] == "ok", table
        assert table["lineage"]["kind"] == "fact"
        assert len(table["data"]["rows"]) == len(SEED_TODO_ROWS)

        series = host.analytics.query(
            "palm-todos-by-priority",
            profile="series",
            series={"x_field": "priority", "y_fields": ["count"]},
        )
        assert series["status"] == "ok", series
        assert series["lineage"]["kind"] == "view"
        assert series["lineage"]["derived_from"] == ["palm-todos"]


def test_todo_builder_commit_persists_kv() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=HostProfile.all_in_one(),
    ) as host:
        register_todo_builder(host.app.repository())
        from palm.patterns.wizard.bindings.compensation.handler import (
            CommitContext,
            default_commit_registry,
        )
        from palm.states import BlackboardState

        engine = host.app.runtime().resource
        if not engine.is_initialized:
            engine.initialize()
        ctx = CommitContext(
            wizard_name="todo-builder",
            state=BlackboardState({}),
            answers={
                "todos": [
                    {"title": "A", "priority": "high"},
                    {"title": "B", "priority": "low"},
                ]
            },
            hook_name="persist_todo_list",
            resource_engine=engine,
        )
        result = default_commit_registry().run("persist_todo_list", ctx)
        assert result.ok, result.error
        assert result.data.get("persisted") is True

        q = host.analytics.query("palm-todos", profile="table")
        assert q["status"] == "ok"
        assert q["meta"]["row_count"] == 2
