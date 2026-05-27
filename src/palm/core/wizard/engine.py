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
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

from palm.config.settings import settings
from palm.core.wizard.context import ContextBuilder, RichContext
from palm.core.wizard.definition import WizardDefinition
from palm.core.wizard.validators import validate_input
from palm.exceptions import (
    BacktrackNotAllowedError,
    InvalidStepError,
    SessionExpiredError,
    SessionNotFoundError,
    ValidationError,
    WizardNotFoundError,
)
from palm.models.common import SessionStatus, StepType
from palm.models.session import WizardSession
from palm.persistence.sqlite import SQLiteSessionStore
from palm.utils.logging import logger
from palm.utils.time import add_seconds, utc_now


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
        self._commit_handlers: dict[str, Callable[[WizardSession], dict[str, Any]]] = commit_handlers or {}

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

        # Always start at introduction (0.2.0 uses full path)
        intro = definition.introduction_step
        intro_path = [intro.slug]
        session.record_path(intro_path, add_to_back_stack=False)

        self.store.save(session)

        context = self._build_rich_context(session, definition, intro, current_path=intro_path)
        context.is_first_step = True

        session.last_rich_context = context.model_dump(mode="json")
        session.ensure_path_consistency()
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

        # 0.2.2: Ensure current_path is always the single source of truth
        session.ensure_path_consistency()

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

        # 0.2.0: Prefer current_path, fall back to legacy current_step_slug for compatibility
        current_path = session.current_path or ([session.current_step_slug] if session.current_step_slug else [])
        current_step = definition.get_step_by_path(current_path) or definition.get_step(session.current_step_slug or "")

        if not current_step:
            raise InvalidStepError(f"Current step '{session.current_step_slug}' not found in definition")

        # Special handling for introduction (must be explicit confirmation)
        if current_step.type == StepType.INTRODUCTION:
            if not self._is_positive_confirmation(value):
                # Re-emit same context with a gentle message
                ctx = self._build_rich_context(session, definition, current_step, current_path=current_path)
                ctx.metadata["last_error"] = "Please type 'confirm', 'yes', or 'y' to continue."
                return ctx
            # Introduction accepted - never add to back stack

        elif value is not None or not current_step.is_composite():
            # Normal validation only for real user input (skip when auto-advancing composites)
            errors = validate_input(value, current_step, session.collected_data)
            if errors:
                raise ValidationError(
                    "Input validation failed",
                    field=current_step.slug,
                    errors=errors,
                )

        # Store the answer only for real user-provided values
        if value is not None:
            field_name = current_step.slug
            session.collected_data[field_name] = self._normalize_value(value, current_step)

        # 0.2.2: Single-source-of-truth navigation loop
        logger.debug(f"process_input: current_path={current_path}, current_step={current_step.slug}")
        next_path = definition.get_next_path(current_path, session.collected_data)

        while next_path is not None:
            next_step = definition.get_step_by_path(next_path)
            if not next_step:
                next_slug = next_path[-1] if next_path else None
                next_step = definition.get_step(next_slug) if next_slug else None

            if not next_step:
                raise InvalidStepError(f"Could not resolve next step from path {next_path}")

            # Record (this is the authoritative write for this step in the path)
            add_to_back = next_step.is_backtrackable
            session.record_path(next_path, add_to_back_stack=add_to_back)

            # 0.2.2: Pure control composites (SEQUENCE / CONDITION) never pause for the user.
            # We auto-descend (or continue after finishing children) inside the same tick.
            if next_step.is_composite() and next_step.type in (StepType.SEQUENCE, StepType.CONDITION):
                logger.debug(f"Auto-descending into composite {next_path} (type={next_step.type})")
                self.store.save(session)
                current_path = next_path
                next_path = definition.get_next_path(current_path, session.collected_data)
                continue

            # Special non-pausing types
            if next_step.type == StepType.ACTION:
                self._execute_action_step(session, next_step)
                self.store.save(session)
                current_path = next_path
                next_path = definition.get_next_path(current_path, session.collected_data)
                continue

            # Pausing step reached (or COMMIT)
            if next_step.type == StepType.COMMIT:
                session.status = SessionStatus.AWAITING_COMMIT
            else:
                session.status = SessionStatus.PAUSED_FOR_INPUT

            self.store.save(session)
            context = self._build_rich_context(session, definition, next_step, current_path=next_path)
            session.last_rich_context = context.model_dump(mode="json")
            session.ensure_path_consistency()
            self.store.save(session)

            logger.debug(f"Session {session_id} paused at path {next_path}")
            return context

        # No more steps
        return self._finalize_session(session, definition, commit_result={"status": "completed_without_commit"})

    def backtrack(self, session_id: str, target: str) -> RichContext:
        """
        Backtrack to a previous step.

        In 0.2.0 `target` can be:
        - A simple slug (finds most recent occurrence)
        - A qualified path string "parent.child.grandchild"

        Supports full hierarchical backtracking.
        """
        session = self.get_session(session_id)
        definition = self.get_definition(session.wizard_id)

        if target not in session.back_stack:
            raise BacktrackNotAllowedError(f"Cannot backtrack to '{target}' - not in back stack")

        logger.info(f"backtrack requested to '{target}' for session {session_id}")

        # Resolve target step (support both slug and dotted path)
        target_path: list[str]
        if "." in target:
            target_path = target.split(".")
        else:
            # Find the last matching path that ends with the slug
            target_path = None
            for p in reversed(session.execution_path_history):
                if p and p[-1] == target:
                    target_path = list(p)
                    break
            if target_path is None:
                target_path = [target]

        target_step = definition.get_step_by_path(target_path) or definition.get_step(target)
        if not target_step or not target_step.is_backtrackable:
            raise BacktrackNotAllowedError(f"Step '{target}' is not backtrackable")

        # Robustly truncate execution_path_history to the target (or last occurrence of the path)
        try:
            if "." in target:
                match_path = target_path
                for i in range(len(session.execution_path_history) - 1, -1, -1):
                    if session.execution_path_history[i] == match_path:
                        session.execution_path_history = session.execution_path_history[:i+1]
                        break
            else:
                # Slug-based: truncate both histories at the last occurrence of the leaf
                for i in range(len(session.execution_path_history) - 1, -1, -1):
                    if session.execution_path_history[i] and session.execution_path_history[i][-1] == target:
                        session.execution_path_history = session.execution_path_history[:i+1]
                        break

                # Also keep step_history consistent (best effort)
                if target in session.step_history:
                    idx = session.step_history.index(target)
                    session.step_history = session.step_history[:idx + 1]
        except Exception as exc:
            logger.warning(f"History truncation encountered issue during backtrack: {exc}")

        popped = session.pop_back_stack_to(target)

        # 0.2.2: Clear data for everything after the target (handles dotted paths properly)
        for key in popped:
            # Remove both the dotted key and the leaf slug
            if key in session.collected_data:
                session.collected_data.pop(key, None)
            leaf = key.split(".")[-1]
            if leaf in session.collected_data:
                logger.debug(f"  clearing collected data for '{leaf}' (from backtrack)")
                session.collected_data.pop(leaf, None)

        session.current_path = list(target_path)
        session.current_step_slug = target_path[-1]
        session.status = SessionStatus.PAUSED_FOR_INPUT

        # 0.2.2: Force consistency after backtrack
        session.ensure_path_consistency()
        self.store.save(session)

        context = self._build_rich_context(session, definition, target_step, current_path=target_path)
        session.last_rich_context = context.model_dump(mode="json")
        self.store.save(session)

        logger.info(f"Session {session_id} successfully backtracked to path {target_path}")
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
        *,
        current_path: list[str] | None = None,
    ) -> RichContext:
        """
        Build a RichContext, optionally applying a dynamic ContextBuilder (0.2.0).

        The builder can override any renderable field at runtime based on collected data.
        """
        path_to_use = current_path or session.current_path or ([step.slug] if step else [])
        breadcrumb = definition.get_breadcrumb(path_to_use)

        allowed_back = [
            s for s in session.back_stack if s != definition.introduction_step.slug
        ]

        input_type = "text"
        if step.type == StepType.CHOICE:
            input_type = "choice"
        elif step.type == StepType.CONFIRM or step.type == StepType.INTRODUCTION:
            input_type = "confirm"
        elif step.type == StepType.SUMMARY:
            input_type = "summary"
        elif step.type in (StepType.DISPLAY, StepType.ACTION, StepType.COMMIT):
            input_type = "none"
        elif step.is_composite():
            input_type = "none"  # composites usually auto-advance

        # Base contextual help (0.1.1 + 0.2.0)
        suggested: str | None = None
        actions: list[str] = []

        if step.type == StepType.INTRODUCTION:
            suggested = "confirm"
            actions = ["Type 'confirm', 'yes', or 'y' to begin the wizard"]
        elif step.type in (StepType.SUMMARY, StepType.COMMIT):
            suggested = "confirm"
            actions = [
                "Type 'confirm', 'yes', or 'commit' to proceed",
                "Use 'back <step-slug>' (or dotted path) to change a previous answer",
            ]
        elif step.type == StepType.CONFIRM:
            suggested = "yes"
            actions = ["Type 'yes' / 'no' or 'confirm' / 'cancel'"]
        elif step.type == StepType.CHOICE and step.choices:
            actions = [f"Choose one of: {', '.join(c.get('value', str(c)) for c in step.choices)}"]
        elif step.is_composite() and step.type == StepType.CONDITION:
            actions = ["Evaluating condition... (auto-advancing)"]
        else:
            if allowed_back:
                actions.append("Use 'back <slug>' to return to a previous step")

        if allowed_back:
            actions.append(f"Backtrackable: {', '.join(allowed_back)}")

        # Start with static values from the step definition
        guidelines = step.guidelines
        choices = step.choices
        validation_rules = [r.model_dump() for r in step.validation_rules]
        metadata = dict(step.metadata)
        step_title = step.title
        prompt = step.prompt or step.title

        # === 0.2.0 Dynamic Context Builder (the powerful new feature) ===
        builder = step.context_builder
        if builder is not None:
            try:
                overrides = builder(session.collected_data, step)
                if isinstance(overrides, dict):
                    if "guidelines" in overrides:
                        guidelines = overrides["guidelines"]
                    if "choices" in overrides:
                        choices = overrides["choices"]
                    if "validation_rules" in overrides:
                        validation_rules = overrides["validation_rules"]
                    if "suggested_input" in overrides:
                        suggested = overrides["suggested_input"]
                    if "available_actions" in overrides:
                        actions = overrides["available_actions"]
                    if "prompt" in overrides:
                        prompt = overrides["prompt"]
                    if "title" in overrides or "step_title" in overrides:
                        step_title = overrides.get("title") or overrides.get("step_title")
                    # Allow full metadata merge
                    if "metadata" in overrides and isinstance(overrides["metadata"], dict):
                        metadata.update(overrides["metadata"])
            except Exception as exc:
                logger.warning(f"ContextBuilder for step '{step.slug}' failed: {exc}")

        # Merge dynamic actions if builder didn't fully replace them
        if allowed_back and "back" not in str(actions).lower():
            actions.append(f"Backtrackable steps: {', '.join(allowed_back)}")

        return RichContext(
            session_id=session.id,
            wizard_id=definition.id,
            wizard_name=definition.name,
            current_step_slug=step.slug,
            current_step_type=step.type,
            step_title=step_title,
            prompt=prompt,
            guidelines=guidelines,
            description=step.description,
            input_type=input_type,
            choices=choices,
            validation_rules=validation_rules,
            required=step.required,
            allowed_back_steps=allowed_back,
            can_backtrack=len(allowed_back) > 0,
            path=list(session.step_history),
            collected_data=dict(session.collected_data),
            status=session.status,
            metadata=metadata,
            suggested_input=suggested,
            available_actions=actions,
            # 0.2.0: expose the full current path for rich UIs
            formatted_summary=breadcrumb or None,
            current_path=list(path_to_use),
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
