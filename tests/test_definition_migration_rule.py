"""Tests for definition migration rules (0.24.2)."""

from __future__ import annotations

from palm.common.persistence.definition_migration import (
    CallableMigrationRule,
    MigrationContext,
    migration_registry,
    register_migration_rule,
    resolve_migration_rule,
)


def setup_function() -> None:
    migration_registry.clear()


def test_register_and_resolve_migration_rule() -> None:
    rule = CallableMigrationRule(
        flow_id="onboard",
        from_revision=1,
        to_revision=2,
        _can_migrate=lambda _ctx: (True, []),
        _migrate_state=lambda ctx: {**ctx.state, "migrated": True},
    )
    register_migration_rule(rule)
    resolved = resolve_migration_rule("onboard", 1, 2)
    assert resolved is rule


def test_resolve_returns_none_when_missing() -> None:
    assert resolve_migration_rule("onboard", 1, 2) is None


def test_callable_rule_migrates_state() -> None:
    rule = CallableMigrationRule(
        flow_id="onboard",
        from_revision=1,
        to_revision=2,
        _can_migrate=lambda _ctx: (True, []),
        _migrate_state=lambda ctx: {**ctx.state, "version": 2},
    )
    ctx = MigrationContext(
        flow_id="onboard",
        from_revision=1,
        to_revision=2,
        instance_id="inst-1",
        state={"answers": {"name": "Ada"}},
    )
    ok, blockers = rule.can_migrate(ctx)
    assert ok is True
    assert blockers == []
    assert rule.migrate_state(ctx) == {"answers": {"name": "Ada"}, "version": 2}


def test_callable_rule_reports_blockers() -> None:
    rule = CallableMigrationRule(
        flow_id="onboard",
        from_revision=1,
        to_revision=2,
        _can_migrate=lambda ctx: ("legacy" not in ctx.state, ["legacy key present"]),
        _migrate_state=lambda ctx: ctx.state,
    )
    ctx = MigrationContext(
        flow_id="onboard",
        from_revision=1,
        to_revision=2,
        instance_id="inst-1",
        state={"legacy": True},
    )
    ok, blockers = rule.can_migrate(ctx)
    assert ok is False
    assert blockers == ["legacy key present"]