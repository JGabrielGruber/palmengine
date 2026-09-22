"""0.68.13 — unused work_drain journal consumer + host redrive facade composted."""

from __future__ import annotations

import inspect

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.workplane.coordinator import WorkPlaneCoordinator
from palm.common.events import consumers as journal_consumers
from palm.common.events.journal import EventJournal
from palm.core.structure import CAPABILITY_WORK_DRAIN
from palm.system.structure.hands import LOCAL_CAPABILITY_HANDS


def test_work_drain_journal_consumer_and_host_redrive_are_gone() -> None:
    assert not hasattr(journal_consumers, "mark_work_drain_caught_up")
    assert not hasattr(journal_consumers, "JOURNAL_CONSUMER_WORK_DRAIN")
    assert not hasattr(journal_consumers, "consume_for_work_drain")
    assert "work_drain" not in journal_consumers.DEFAULT_JOURNAL_CONSUMERS
    assert "mark_work_drain_caught_up" not in inspect.getsource(journal_consumers)
    assert not hasattr(ApplicationHost, "redrive_journal")
    assert not hasattr(WorkPlaneCoordinator, "redrive_journal")


def test_work_drain_organ_and_journal_redrive_stay() -> None:
    assert CAPABILITY_WORK_DRAIN == "work_drain"
    assert "work_drain" in LOCAL_CAPABILITY_HANDS
    assert hasattr(EventJournal, "redrive")
    assert hasattr(EventJournal, "consume")
