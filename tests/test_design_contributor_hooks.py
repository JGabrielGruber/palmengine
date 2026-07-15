"""Tests for pattern-owned design contributor hooks (0.25.4)."""

from __future__ import annotations

import pytest

from palm.common.patterns._registry import (
    DesignContributorHook,
    clear_design_contributor_hooks,
    get_design_contributor_hook,
    iter_design_contributor_hooks,
    register_design_contributor_hook,
)
from palm.services.design.contributors import (
    reset_design_contributor_wiring,
    wire_builtin_design_contributors,
)
from palm.services.design.registry import clear_design_contributors, iter_design_contributors


@pytest.fixture(autouse=True)
def _isolate_service_registry() -> None:
    clear_design_contributors()
    reset_design_contributor_wiring()
    yield
    clear_design_contributors()
    reset_design_contributor_wiring()


def _ensure_wizard_hook() -> None:
    from palm.patterns.wizard.app import wizard_app

    wizard_app.register()


def test_wizard_registers_design_contributor_hook_on_pattern_import() -> None:
    _ensure_wizard_hook()

    hook = get_design_contributor_hook("wizard")
    assert hook is not None
    assert hook.pattern_name == "wizard"
    assert hook.register.__name__ == "register_wizard_design_contributor"


def _ensure_pipeline_hook() -> None:
    from palm.patterns.pipeline.app import pipeline_app

    pipeline_app.register()


def test_wire_drains_pattern_hooks_into_design_registry() -> None:
    _ensure_wizard_hook()
    _ensure_pipeline_hook()

    assert len(iter_design_contributors()) == 0
    wire_builtin_design_contributors()
    contributor_ids = {row.contributor_id for row in iter_design_contributors()}
    # wiring also registers built-in provider/dashboard design contributors
    # (kv, file, dashboard); assert the drained pattern hooks are present.
    assert {"pipeline", "wizard"} <= contributor_ids


def test_custom_hook_registers_via_wire() -> None:
    clear_design_contributor_hooks()
    calls: list[str] = []

    def _register() -> None:
        from palm.services.design.registry import DesignContributor, register_design_contributor

        calls.append("registered")
        register_design_contributor(
            DesignContributor(
                contributor_id="demo-pattern",
                validate=lambda _body, _ctx: (True, []),
            )
        )

    register_design_contributor_hook(
        DesignContributorHook(pattern_name="demo-pattern", register=_register)
    )
    wire_builtin_design_contributors()

    assert calls == ["registered"]
    contributor_ids = {row.contributor_id for row in iter_design_contributors()}
    assert "demo-pattern" in contributor_ids

    _ensure_wizard_hook()


def test_iter_design_contributor_hooks_is_stable() -> None:
    clear_design_contributor_hooks()
    register_design_contributor_hook(
        DesignContributorHook(pattern_name="zebra", register=lambda: None)
    )
    register_design_contributor_hook(
        DesignContributorHook(pattern_name="alpha", register=lambda: None)
    )
    names = [hook.pattern_name for hook in iter_design_contributor_hooks()]
    assert names == ["alpha", "zebra"]

    _ensure_wizard_hook()