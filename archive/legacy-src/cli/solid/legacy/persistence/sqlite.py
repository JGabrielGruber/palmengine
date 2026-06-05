"""
SQLite persistence using SQLAlchemy 2.0+.

Stores WizardSession state. WizardDefinitions themselves are code-defined
and registered at runtime (not persisted).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from palm.cli.solid.legacy.models.session import WizardSession
from palm.cli.solid.legacy.utils.time import utc_now
from palm.config.settings import settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base."""


class DBSession(Base):
    """Database row representing a persisted wizard session."""

    __tablename__ = "wizard_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    wizard_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    current_step_slug: Mapped[str | None] = mapped_column(String(64))

    collected_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    step_history: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    back_stack: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    commit_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    error_step: Mapped[str | None] = mapped_column(String(64))

    last_rich_context: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Internal
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(db_path: str | None = None) -> Engine:
    """Lazily create and cache the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        path = db_path or str(settings.db_path)
        _engine = create_engine(
            f"sqlite:///{path}",
            echo=False,
            connect_args={
                "check_same_thread": False
            },  # safe for multiprocessing + single writer pattern
            pool_pre_ping=True,
        )
        Base.metadata.create_all(_engine)
    return _engine


def get_session_maker() -> sessionmaker[Session]:
    """Return a sessionmaker bound to the engine."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


class SQLiteSessionStore:
    """
    High-level store for WizardSession objects.

    All methods work with Pydantic WizardSession models, transparently
    converting to/from the DB row model.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.engine = get_engine(db_path)
        self.SessionLocal = get_session_maker()

    def _to_db(self, session: WizardSession) -> DBSession:
        return DBSession(
            id=session.id,
            wizard_id=session.wizard_id,
            status=session.status.value,
            current_step_slug=session.current_step_slug,
            collected_data=session.collected_data,
            step_history=session.step_history,
            back_stack=session.back_stack,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            commit_result=session.commit_result,
            error=session.error,
            error_step=session.error_step,
            last_rich_context=session.last_rich_context,
        )

    def _from_db(self, row: DBSession) -> WizardSession:
        return WizardSession(
            id=row.id,
            wizard_id=row.wizard_id,
            status=row.status,  # type: ignore[arg-type]
            current_step_slug=row.current_step_slug,
            collected_data=row.collected_data or {},
            step_history=row.step_history or [],
            back_stack=row.back_stack or [],
            created_at=row.created_at,
            last_activity_at=row.last_activity_at,
            expires_at=row.expires_at,
            commit_result=row.commit_result,
            error=row.error,
            error_step=row.error_step,
            last_rich_context=row.last_rich_context,
        )

    def save(self, session: WizardSession) -> None:
        """Insert or update a session."""
        session.touch()
        with self.SessionLocal() as db:
            existing = db.get(DBSession, session.id)
            if existing:
                # Update fields
                existing.status = session.status.value
                existing.current_step_slug = session.current_step_slug
                existing.collected_data = session.collected_data
                existing.step_history = session.step_history
                existing.back_stack = session.back_stack
                existing.last_activity_at = session.last_activity_at
                existing.expires_at = session.expires_at
                existing.commit_result = session.commit_result
                existing.error = session.error
                existing.error_step = session.error_step
                existing.last_rich_context = session.last_rich_context
            else:
                db.add(self._to_db(session))
            db.commit()

    def get(self, session_id: str) -> WizardSession | None:
        with self.SessionLocal() as db:
            row = db.get(DBSession, session_id)
            return self._from_db(row) if row else None

    def get_by_wizard(self, wizard_id: str, limit: int = 50) -> list[WizardSession]:
        with self.SessionLocal() as db:
            stmt = (
                select(DBSession)
                .where(DBSession.wizard_id == wizard_id)
                .order_by(DBSession.last_activity_at.desc())
                .limit(limit)
            )
            rows = db.execute(stmt).scalars().all()
            return [self._from_db(r) for r in rows]

    def list_active(self, limit: int = 100) -> list[WizardSession]:
        with self.SessionLocal() as db:
            stmt = (
                select(DBSession)
                .where(DBSession.status.in_(["running", "paused_for_input", "awaiting_commit"]))
                .order_by(DBSession.last_activity_at.desc())
                .limit(limit)
            )
            rows = db.execute(stmt).scalars().all()
            return [self._from_db(r) for r in rows]

    def delete(self, session_id: str) -> bool:
        with self.SessionLocal() as db:
            row = db.get(DBSession, session_id)
            if row:
                db.delete(row)
                db.commit()
                return True
            return False

    def cleanup_expired(self) -> int:
        """Delete sessions whose expires_at < now. Returns count deleted."""
        now = utc_now()
        with self.SessionLocal() as db:
            stmt = select(DBSession).where(
                DBSession.expires_at.is_not(None),
                DBSession.expires_at < now,
            )
            rows = db.execute(stmt).scalars().all()
            count = len(rows)
            for r in rows:
                db.delete(r)
            db.commit()
            return count
