"""Definition migration rules — revision-to-revision instance state upgrades."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class MigrationContext:
    """Inputs for evaluating and applying a definition migration."""

    flow_id: str
    from_revision: int
    to_revision: int
    instance_id: str
    state: dict[str, Any]


@runtime_checkable
class DefinitionMigrationRule(Protocol):
    """Upgrade instance state from one flow revision to another."""

    flow_id: str
    from_revision: int
    to_revision: int

    def can_migrate(self, ctx: MigrationContext) -> tuple[bool, list[str]]:
        """Return whether migration is allowed and optional blocker messages."""

    def migrate_state(self, ctx: MigrationContext) -> dict[str, Any]:
        """Return migrated blackboard/state snapshot."""


@dataclass(frozen=True)
class CallableMigrationRule:
    """Concrete migration rule backed by callables (tests and simple extensions)."""

    flow_id: str
    from_revision: int
    to_revision: int
    _can_migrate: Callable[[MigrationContext], tuple[bool, list[str]]]
    _migrate_state: Callable[[MigrationContext], dict[str, Any]]

    def can_migrate(self, ctx: MigrationContext) -> tuple[bool, list[str]]:
        return self._can_migrate(ctx)

    def migrate_state(self, ctx: MigrationContext) -> dict[str, Any]:
        return self._migrate_state(ctx)


class _MigrationRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rules: dict[tuple[str, int, int], DefinitionMigrationRule] = {}

    def register(self, rule: DefinitionMigrationRule) -> None:
        key = (rule.flow_id, rule.from_revision, rule.to_revision)
        with self._lock:
            self._rules[key] = rule

    def resolve(
        self,
        flow_id: str,
        from_revision: int,
        to_revision: int,
    ) -> DefinitionMigrationRule | None:
        with self._lock:
            return self._rules.get((flow_id, from_revision, to_revision))

    def clear(self) -> None:
        with self._lock:
            self._rules.clear()


migration_registry = _MigrationRegistry()


def register_migration_rule(rule: DefinitionMigrationRule) -> None:
    """Register a migration rule for ``(flow_id, from_revision, to_revision)``."""
    migration_registry.register(rule)


def resolve_migration_rule(
    flow_id: str,
    from_revision: int,
    to_revision: int,
) -> DefinitionMigrationRule | None:
    """Return a registered rule for the revision pair, if any."""
    return migration_registry.resolve(flow_id, from_revision, to_revision)


__all__ = [
    "CallableMigrationRule",
    "DefinitionMigrationRule",
    "MigrationContext",
    "migration_registry",
    "register_migration_rule",
    "resolve_migration_rule",
]