"""Tests for Django-style modular pattern/provider/storage apps."""

from __future__ import annotations

import importlib

import pytest

from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.patterns._apps import INSTALLED_PATTERNS
from palm.patterns._registry import get_builder, registered_builders
from palm.providers._apps import INSTALLED_PROVIDERS
from palm.common.storage import StorageFactory
from palm.storages._apps import CORE_STORAGES, INSTALLED_STORAGES, OPTIONAL_STORAGES


@pytest.fixture(autouse=True)
def _reload_apps() -> None:
    """Ensure registries are populated for isolated assertions."""
    importlib.import_module("palm.patterns")
    importlib.import_module("palm.providers")
    importlib.import_module("palm.storages")


def test_installed_pattern_apps_register() -> None:
    assert set(INSTALLED_PATTERNS) == {"dag", "etl", "wizard"}
    for name in INSTALLED_PATTERNS:
        pattern_registry.get(name)
    assert set(registered_builders()) == set(INSTALLED_PATTERNS)
    for name in INSTALLED_PATTERNS:
        assert get_builder(name) is not None


def test_installed_provider_apps_register() -> None:
    assert set(INSTALLED_PROVIDERS) == {"rest", "graphql", "postgres"}
    for name in INSTALLED_PROVIDERS:
        provider_registry.get(name)


def test_installed_storage_apps_register() -> None:
    assert set(INSTALLED_STORAGES) == {"memory", "postgres", "mongodb", "filesystem"}
    assert set(CORE_STORAGES) == {"memory", "filesystem"}
    assert set(OPTIONAL_STORAGES) == {"postgres", "mongodb"}
    for name in CORE_STORAGES:
        storage_registry.get(name)
    for name in OPTIONAL_STORAGES:
        StorageFactory.ensure_registered(name)
        storage_registry.get(name)


def test_wizard_handler_exports() -> None:
    from palm.patterns.wizard import CommitRegistry
    from palm.patterns.wizard.handler import CommitRegistry as HandlerRegistry

    assert CommitRegistry is HandlerRegistry