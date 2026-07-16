"""Todos pack — materialize + query; bootstrap package load."""

from __future__ import annotations

from examples.definitions.todos import register_definitions as register_todos
from examples.definitions.todos.resources import (
    SEED_TODO_ROWS,
    materialize_todo_analytics,
)
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings


def test_todo_package_materialize_and_query() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        register_todos(host.app.repository())
        result = materialize_todo_analytics(host.execution.providers)
        assert result["todo_rows"] == len(SEED_TODO_ROWS)
        assert result["fact_put"].get("success") is True

        names = {r["dataset"] for r in host.analytics.list_datasets()}
        assert "palm-todos" in names
        assert "palm-todos-by-priority" in names

        table = host.analytics.query(
            "palm-todos", profile="table", select=["title", "priority"]
        )
        assert table["status"] == "ok", table
        assert len(table["data"]["rows"]) == len(SEED_TODO_ROWS)

        series = host.analytics.query(
            "palm-todos-by-priority",
            profile="series",
            series={"x_field": "priority", "y_fields": ["count"]},
        )
        assert series["status"] == "ok", series
        assert series["meta"].get("virtual") is True
        assert "palm-todos" in (series["lineage"].get("derived_from") or [])


def test_bootstrap_loads_todos_and_coconut_packs() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=True),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        flows = {f["name"] for f in host.definitions.list_flows()}
        assert "todo-builder" in flows
        assert "todo-analytics" in flows
        assert "coconut-npc" in flows
        resources = {r["name"] for r in host.definitions.list_resources()}
        assert "palm-todos" in resources
        assert "load-coconut-player" in resources
