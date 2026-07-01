"""Tests for application-level assist contributor registry."""

from __future__ import annotations

import pytest

from palm.app.assist_registry import (
    AppAssistContributor,
    clear_app_assist_contributors,
    iter_app_assist_contributors,
    register_app_assist_contributor,
)
from palm.services.assist.registry import AssistContributor, clear_assist_contributors, scenario_by_id


@pytest.fixture(autouse=True)
def _isolate_registries() -> None:
    clear_app_assist_contributors()
    clear_assist_contributors()
    yield
    clear_app_assist_contributors()
    clear_assist_contributors()


def test_register_app_assist_contributor() -> None:
    register_app_assist_contributor(
        AppAssistContributor(
            app_name="demo-app",
            contributor=AssistContributor(
                contributor_id="demo-app",
                scenario_id="demo-scenario",
                flow_id="flow-demo",
                summary="Demo scenario",
            ),
        )
    )
    rows = iter_app_assist_contributors()
    assert len(rows) == 1
    assert rows[0].app_name == "demo-app"
    found = scenario_by_id("demo-scenario")
    assert found is not None
    assert found.flow_id == "flow-demo"