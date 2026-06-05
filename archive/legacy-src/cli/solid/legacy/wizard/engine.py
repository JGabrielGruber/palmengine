"""
WizardEngine - the heart of Palm's interactive workflow execution.

Responsibilities:
- Start sessions from WizardDefinition
- Advance on user "ticks" (input)
- Generate RichContext before every interaction point
- Handle validation
- Support backtracking by step slug
- Persist and resume sessions
- Execute commit step (transactional boundary)

The engine is deliberately UI-agnostic. All interaction goes through RichContext.

DEPRECATION NOTICE
------------------
This module is part of Palm's legacy reference implementation.
It was moved from palm/core/wizard/ into cli/solid/legacy/ during the 0.3.0-dev
clean-core migration.

This code is preserved ONLY as a working historical snapshot.
New code MUST NOT import from palm.cli.solid.legacy.* (except inside this package).
Future wizard implementations will be built cleanly on top of palm.core.behavior_tree.

Last updated: 0.3.0-dev migration
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.cli.solid.legacy.exceptions import (
    BacktrackNotAllowedError,
    InvalidStepError,
    SessionExpiredError,
    SessionNotFoundError,
    ValidationError,
    WizardNotFoundError,
)
from palm.cli.solid.legacy.models.common import SessionStatus, StepType
from palm.cli.solid.legacy.models.session import WizardSession
from palm.cli.solid.legacy.persistence.sqlite import SQLiteSessionStore
from palm.cli.solid.legacy.utils.time import add_seconds, utc_now
from palm.cli.solid.legacy.wizard.context import RichContext
from palm.cli.solid.legacy.wizard.definition import WizardDefinition
from palm.cli.solid.legacy.wizard.validators import validate_input
from palm.config.settings import settings
from palm.utils.logging import logger


class WizardEngine:
    """
    Stateless (per call) engine that drives wizard sessions.

    Thread/process safe as long as the underlying store is.
    Designed to be used from the Orchestrator or directly from a REPL.
    """

    def __init__(
        self,
        store: SQLiteSessionStore | None = None,
        commit_handlers: dict[str, Callable[[WizardSession], dict[str, Any]]] | None = None,
    ) -> None:
        self.store = store or SQLiteSessionStore()
        self._definitions: dict[str, WizardDefinition] = {}
        self._commit_handlers: dict[str, Callable[[WizardSession], dict[str, Any]]] = (
            commit_handlers or {}
        )

    # ------------------------------------------------------------------
    # Commit handler management
    # ------------------------------------------------------------------

    def register_commit_handler(
        self,
        name: str,
        handler: Callable[[WizardSession], dict[str, Any]],
    ) -> None:
        """Register (or overwrite) a named commit handler."""
        self._commit_handlers[name] = handler
        logger.debug(f"Registered commit handler: {name}")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        definition: WizardDefinition,
        *,
        commit_handlers: dict[str, Callable[[WizardSession], dict[str, Any]]] | None = None,
    ) -> None:
        """
        Register (or overwrite) a wizard definition.

        Optionally pass commit_handlers that will be registered together with
        the wizard. This is the recommended way for wizard authors to bundle
        their transactional commit logic.
        """
        self._definitions[definition.id] = definition
        logger.info(f"Registered wizard: {definition.id} v{definition.version}")

        if commit_handlers:
            for name, handler in commit_handlers.items():
                self.register_commit_handler(name, handler)
            logger.debug(
                f"Registered {len(commit_handlers)} commit handler(s) for wizard '{definition.id}'"
            )

    def get_definition(self, wizard_id: str) -> WizardDefinition:
        if wizard_id not in self._definitions:
            raise WizardNotFoundError(f"Wizard '{wizard_id}' is not registered")
        return self._definitions[wizard_id]

    def list_wizards(self) -> list[dict[str, Any]]:
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "version": d.version,
                "step_count": len(d.steps),
            }
            for d in self._definitions.values()
        ]

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(
        self,
        wizard_id: str,
        *,
        ttl_seconds: int | None = None,
        initial_data: dict[str, Any] | None = None,
    ) -> tuple[WizardSession, RichContext]:
        """
        Create a brand new session and immediately advance to the first (introduction) step.

        Returns (session, initial_rich_context).
        """
        definition = self.get_definition(wizard_id)

        ttl = ttl_seconds or settings.default_session_ttl_seconds
        now = utc_now()

        session = WizardSession(
            wizard_id=wizard_id,
            status=SessionStatus.RUNNING,
            created_at=now,
            last_activity_at=now,
            expires_at=add_seconds(now, ttl),
            collected_data=initial_data or {},
        )

        # Always start at introduction
        intro = definition.introduction_step
        session.record_step(intro.slug, add_to_back_stack=False)  # never backtrack to intro

        self.store.save(session)

        context = self._build_rich_context(session, definition, intro)
        context.is_first_step = True

        session.last_rich_context = context.model_dump(mode="json")
        self.store.save(session)

        logger.info(f"Started new session {session.id} for wizard '{wizard_id}'")
        return session, context

    def get_session(self, session_id: str, *, touch: bool = True) -> WizardSession:
        session = self.store.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        if session.is_expired():
            session.status = SessionStatus.EXPIRED
            self.store.save(session)
            raise SessionExpiredError(f"Session {session_id} has expired")

        if touch:
            session.touch()
            self.store.save(session)
        return session

    # ------------------------------------------------------------------
    # Core tick: process user input
    # ------------------------------------------------------------------

    def process_input(
        self,
        session_id: str,
        value: Any,
        *,
        raw_input: str | None = None,
    ) -> RichContext:
        """
        The primary "tick" method.

        The user (via any UI) provides a value for the current step.
        Engine validates, stores, advances, and returns the *next* RichContext
        (or final committed state).
        """
        session = self.get_session(session_id)
        definition = self.get_definition(session.wizard_id)
        current_step = definition.get_step(session.current_step_slug or "")

        if not current_step:
            raise InvalidStepError(
                f"Current step '{session.current_step_slug}' not found in definition"
            )

        # Special handling for introduction (must be explicit confirmation)
        if current_step.type == StepType.INTRODUCTION:
            if not self._is_positive_confirmation(value):
                # Re-emit same context with a gentle message
                ctx = self._build_rich_context(session, definition, current_step)
                ctx.metadata["last_error"] = "Please type 'confirm', 'yes', or 'y' to continue."
                return ctx
            # Introduction accepted - never add to back stack

        else:
            # Normal validation for all other input steps
            errors = validate_input(value, current_step, session.collected_data)
            if errors:
                raise ValidationError(
                    "Input validation failed",
                    field=current_step.slug,
                    errors=errors,
                )

        # Store the answer
        field_name = current_step.slug
        session.collected_data[field_name] = self._normalize_value(value, current_step)

        # Advance
        next_slug = definition.get_next_step_slug(current_step.slug, session.collected_data)

        if next_slug is None:
            # We have reached terminal state without an explicit COMMIT step
            return self._finalize_session(
                session, definition, commit_result={"status": "completed_without_commit"}
            )

        next_step = definition.get_step(next_slug)
        if not next_step:
            raise InvalidStepError(
                f"Next step '{next_slug}' declared but not present in definition"
            )

        # Record navigation
        # A step is added to the back stack if *it* declares itself backtrackable.
        # We intentionally ignore the previous step's flag (so we can back from steps after introduction).
        add_to_back = next_step.is_backtrackable
        session.record_step(next_step.slug, add_to_back_stack=add_to_back)

        # Special step types that may immediately pause or auto-advance
        if next_step.type == StepType.COMMIT:
            session.status = SessionStatus.AWAITING_COMMIT
            self.store.save(session)
            # Return a special context that tells the UI "ready to commit"
            return self._build_rich_context(session, definition, next_step)

        if next_step.type == StepType.ACTION:
            # Execute side effect immediately (no user input)
            self._execute_action_step(session, next_step)
            # Recurse to next step (tail call style)
            return self.process_input(session_id, value=None)  # value ignored for action

        # Normal case: pause and emit RichContext for the new step
        session.status = SessionStatus.PAUSED_FOR_INPUT
        self.store.save(session)

        context = self._build_rich_context(session, definition, next_step)
        session.last_rich_context = context.model_dump(mode="json")
        self.store.save(session)

        logger.debug(f"Session {session_id} advanced to step '{next_step.slug}'")
        return context

    def backtrack(self, session_id: str, target_slug: str) -> RichContext:
        """
        Backtrack the session to a previous step by slug.

        Rules:
        - Cannot backtrack to or before the introduction step
        - Target must be in the current back_stack
        - All data collected after the target step is discarded
        """
        session = self.get_session(session_id)
        definition = self.get_definition(session.wizard_id)

        if target_slug not in session.back_stack:
            raise BacktrackNotAllowedError(
                f"Cannot backtrack to '{target_slug}' - not in back stack"
            )

        target_step = definition.get_step(target_slug)
        if not target_step or not target_step.is_backtrackable:
            raise BacktrackNotAllowedError(f"Step '{target_slug}' is not backtrackable")

        # Remove future history
        try:
            idx = session.step_history.index(target_slug)
            session.step_history = session.step_history[: idx + 1]
        except ValueError:
            pass

        # Clean collected data for steps after target
        popped = session.pop_back_stack_to(target_slug)

        # Remove any data keys that were collected in the popped steps
        for slug in popped:
            session.collected_data.pop(slug, None)

        session.current_step_slug = target_slug
        session.status = SessionStatus.PAUSED_FOR_INPUT

        self.store.save(session)

        context = self._build_rich_context(session, definition, target_step)
        session.last_rich_context = context.model_dump(mode="json")
        self.store.save(session)

        logger.info(f"Session {session_id} backtracked to step '{target_slug}'")
        return context

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def commit(self, session_id: str) -> dict[str, Any]:
        """
        Execute the final transactional commit for a session.

        The session must be at a COMMIT step (or the engine will treat the current
        state as ready for commit).
        """
        session = self.get_session(session_id)
        definition = self.get_definition(session.wizard_id)

        # Find commit handler
        handler_name = definition.on_commit_hook or "default"
        handler = self._commit_handlers.get(handler_name)

        if handler is None:
            # Default no-op handler (useful for development)
            def default_handler(s: WizardSession) -> dict[str, Any]:
                return {
                    "status": "committed",
                    "wizard": definition.id,
                    "session": s.id,
                    "collected_keys": list(s.collected_data.keys()),
                    "timestamp": utc_now().isoformat(),
                }

            handler = default_handler

        try:
            logger.info(f"Executing commit for session {session_id} using handler '{handler_name}'")
            result = handler(session)
            logger.info(f"Commit succeeded for session {session_id}")
            return self._finalize_session(session, definition, commit_result=result)
        except Exception as exc:
            logger.exception(f"Commit failed for session {session_id}: {exc}")
            session.status = SessionStatus.FAILED
            session.error = str(exc)
            session.error_step = session.current_step_slug
            self.store.save(session)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_rich_context(
        self,
        session: WizardSession,
        definition: WizardDefinition,
        step: StepDefinition,
    ) -> RichContext:
        allowed_back = [s for s in session.back_stack if s != definition.introduction_step.slug]

        input_type = "text"
        if step.type == StepType.CHOICE:
            input_type = "choice"
        elif step.type == StepType.CONFIRM or step.type == StepType.INTRODUCTION:
            input_type = "confirm"
        elif step.type == StepType.SUMMARY:
            input_type = "summary"
        elif step.type in (StepType.DISPLAY, StepType.ACTION, StepType.COMMIT):
            input_type = "none"

        # Build contextual help (new in 0.1.1)
        suggested: str | None = None
        actions: list[str] = []

        if step.type == StepType.INTRODUCTION:
            suggested = "confirm"
            actions = ["Type 'confirm', 'yes', or 'y' to begin the wizard"]
        elif step.type in (StepType.SUMMARY, StepType.COMMIT):
            suggested = "confirm"
            actions = [
                "Type 'confirm', 'yes', or 'commit' to proceed",
                "Use 'back <step-slug>' to change a previous answer",
            ]
        elif step.type == StepType.CONFIRM:
            suggested = "yes"
            actions = ["Type 'yes' / 'no' or 'confirm' / 'cancel'"]
        elif step.type == StepType.CHOICE and step.choices:
            actions = [f"Choose one of: {', '.join(c.get('value', str(c)) for c in step.choices)}"]
        else:
            if allowed_back:
                actions.append("Use 'back <slug>' to return to a previous step")

        if allowed_back:
            actions.append(f"Backtrackable steps: {', '.join(allowed_back)}")

        return RichContext(
            session_id=session.id,
            wizard_id=definition.id,
            wizard_name=definition.name,
            current_step_slug=step.slug,
            current_step_type=step.type,
            step_title=step.title,
            prompt=step.prompt or step.title,
            guidelines=step.guidelines,
            description=step.description,
            input_type=input_type,
            choices=step.choices,
            validation_rules=[r.model_dump() for r in step.validation_rules],
            required=step.required,
            allowed_back_steps=allowed_back,
            can_backtrack=len(allowed_back) > 0,
            path=list(session.step_history),
            collected_data=dict(session.collected_data),
            status=session.status,
            metadata=step.metadata,
            suggested_input=suggested,
            available_actions=actions,
        )

    def _is_positive_confirmation(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"y", "yes", "confirm", "ok", "continue", "true", "1"}
        return False

    def _normalize_value(self, value: Any, step: StepDefinition) -> Any:
        if step.type == StepType.USER_INPUT:
            if step.input_schema and step.input_schema.get("type") == "integer":
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return value
        return value

    def _execute_action_step(self, session: WizardSession, step: StepDefinition) -> None:
        """Hook for side effects. For skeleton we just log in metadata."""
        session.collected_data[f"__action_{step.slug}"] = {
            "executed_at": utc_now().isoformat(),
            "step": step.slug,
        }

    def _finalize_session(
        self,
        session: WizardSession,
        definition: WizardDefinition,
        *,
        commit_result: dict[str, Any],
    ) -> RichContext:
        session.status = SessionStatus.COMMITTED
        session.commit_result = commit_result
        session.current_step_slug = None
        self.store.save(session)
        logger.info(f"Session {session.id} committed successfully")

        # Return a terminal RichContext
        return RichContext(
            session_id=session.id,
            wizard_id=definition.id,
            wizard_name=definition.name,
            current_step_slug="__committed__",
            current_step_type=StepType.COMMIT,
            step_title="Completed",
            prompt="Wizard completed successfully.",
            status=SessionStatus.COMMITTED,
            collected_data=dict(session.collected_data),
            path=list(session.step_history),
            metadata={"commit_result": commit_result},
        )

    # ------------------------------------------------------------------
    # Admin / introspection helpers
    # ------------------------------------------------------------------

    def get_status(self, session_id: str) -> dict[str, Any]:
        session = self.store.get(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return {
            "id": session.id,
            "wizard_id": session.wizard_id,
            "status": session.status.value,
            "current_step": session.current_step_slug,
            "collected_keys": list(session.collected_data.keys()),
            "history_length": len(session.step_history),
            "can_backtrack": len(session.back_stack) > 1,
            "created_at": session.created_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        }
