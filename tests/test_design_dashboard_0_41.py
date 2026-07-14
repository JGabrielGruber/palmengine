"""0.41.2 — design propose/publish dashboard."""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings
from palm.services.analytics.dashboard_design import validate_dashboard_body
from palm.services.analytics.dashboards import clear_dashboards, get_dashboard


def test_validate_dashboard_body_ok() -> None:
    ok, blockers, dash = validate_dashboard_body(
        {
            "name": "demo",
            "tiles": [
                {"id": "t1", "dataset": "palm-todos", "profile": "table"},
            ],
        }
    )
    assert ok, blockers
    assert dash is not None
    assert dash.name == "demo"


def test_validate_dashboard_rejects_bad_profile() -> None:
    ok, blockers, _ = validate_dashboard_body(
        {
            "name": "x",
            "tiles": [{"id": "t", "dataset": "d", "profile": "pie"}],
        }
    )
    assert not ok
    assert any("profile" in b for b in blockers)


def test_publish_dashboard_registers() -> None:
    clear_dashboards()
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=HostProfile.all_in_one(),
    ) as host:
        out = host.design.publish_dashboard(
            {
                "name": "design-dash-test",
                "title": "From design",
                "tiles": [
                    {
                        "id": "jobs",
                        "dataset": "palm-system-jobs",
                        "profile": "table",
                        "limit": 10,
                    }
                ],
            }
        )
        assert out.get("status") == "committed", out
        assert out.get("dashboard") == "design-dash-test"
        assert get_dashboard("design-dash-test") is not None
    clear_dashboards()
