"""
Orchestrator - the top-level coordinator of the Palm engine.

It wires together:
- WizardEngine (interactive sessions)
- ProcessManager (background workers)
- EventBus (observability)
- Persistence

This is the primary object a daemon, TUI, or API server would hold.

DEPRECATION NOTICE
------------------
This module is part of Palm's legacy reference implementation.
It was moved from palm/core/ into cli/solid/legacy/ during the 0.3.0-dev
clean-core migration.

This code is preserved ONLY as a working historical snapshot.
New code MUST NOT import from palm.cli.solid.legacy.* (except inside this package).
Future orchestration will be rebuilt on top of palm.core.behavior_tree.

Last updated: 0.3.0-dev migration
"""

from __future__ import annotations

import threading
import time
from typing import Any

from palm.cli.solid.legacy.events import EventBus
from palm.cli.solid.legacy.persistence.sqlite import SQLiteSessionStore
from palm.cli.solid.legacy.process_manager import ProcessManager
from palm.cli.solid.legacy.wizard.engine import WizardEngine
from palm.cli.solid.legacy.workflow.registry import WorkflowRegistry
from palm.config.settings import settings
from palm.utils.logging import logger


class Orchestrator:
    """
    Central facade for the Palm engine.

    In production this would be instantiated once per process (or per node).
    """

    def __init__(
        self,
        store: SQLiteSessionStore | None = None,
        event_bus: EventBus | None = None,
        process_manager: ProcessManager | None = None,
    ) -> None:
        self.store = store or SQLiteSessionStore()
        self.event_bus = event_bus or EventBus()
        self.process_manager = process_manager or ProcessManager()

        self.wizard_engine = WizardEngine(store=self.store)
        self.workflow_registry = WorkflowRegistry()

        self._cleanup_thread: threading.Thread | None = None
        self._stop_cleanup = threading.Event()

        # Start background session cleanup
        self._start_session_cleanup()

        # Emit a startup event
        self.event_bus.publish_named("orchestrator.started", {})
        logger.info("Orchestrator initialized (with background cleanup)")

    def register_wizard(self, definition: Any) -> None:
        """Convenience passthrough."""
        self.wizard_engine.register(definition)

    def start_wizard_session(self, wizard_id: str, **kwargs: Any) -> tuple[Any, Any]:
        session, ctx = self.wizard_engine.start_session(wizard_id, **kwargs)
        self.event_bus.publish_named(
            "wizard.session.started",
            {"session_id": session.id, "wizard_id": wizard_id},
        )
        return session, ctx

    def _start_session_cleanup(self) -> None:
        """Start a daemon thread that periodically removes expired sessions."""
        interval = settings.session_cleanup_interval_seconds

        def _cleanup_loop() -> None:
            logger.info(f"Session cleanup thread started (interval={interval}s)")
            while not self._stop_cleanup.is_set():
                try:
                    deleted = self.store.cleanup_expired()
                    if deleted > 0:
                        logger.info(f"Cleaned up {deleted} expired session(s)")
                except Exception as exc:
                    logger.warning(f"Session cleanup error: {exc}")

                # Sleep in small increments so we can exit promptly
                for _ in range(interval):
                    if self._stop_cleanup.is_set():
                        break
                    time.sleep(1)

            logger.info("Session cleanup thread stopped")

        self._cleanup_thread = threading.Thread(
            target=_cleanup_loop,
            name="palm-session-cleanup",
            daemon=True,
        )
        self._cleanup_thread.start()

    def shutdown(self) -> None:
        """Gracefully stop background workers and the orchestrator."""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2.0)

        self.process_manager.shutdown_all()
        self.event_bus.publish_named("orchestrator.shutdown", {})
        logger.info("Orchestrator shutdown complete")
