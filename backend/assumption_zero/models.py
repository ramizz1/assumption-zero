"""SQLAlchemy database models and session management."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from assumption_zero.config import get_settings


class Base(DeclarativeBase):
    pass


class AnalysisRecord(Base):
    """Persisted analysis record. Full JSON is stored in input_data / result_data."""

    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True)
    status = Column(String(20), nullable=False, default="pending")
    stage = Column(String(40), nullable=False, default="clarifying_idea")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    input_data = Column(Text, nullable=False)   # IdeaInput as JSON
    result_data = Column(Text, nullable=True)   # AnalysisResult as JSON (updated incrementally)
    is_demo = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)

    def set_result(self, result_dict: dict) -> None:
        self.result_data = json.dumps(result_dict, default=str)

    def get_result(self) -> Optional[dict]:
        if self.result_data:
            return json.loads(self.result_data)
        return None


# ── Sync engine (used by tests and CLI) ──────────────────────────────────────

_sync_engine = None
_SyncSession = None


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        _sync_engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(_sync_engine)
    return _sync_engine


def get_sync_session() -> Session:
    global _SyncSession
    if _SyncSession is None:
        _SyncSession = sessionmaker(bind=get_sync_engine(), autoflush=False)
    return _SyncSession()


# ── Async engine (used by FastAPI) ────────────────────────────────────────────

_async_engine = None
_AsyncSession = None


def get_async_engine():
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        # Convert sqlite:/// to sqlite+aiosqlite:///
        url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        _async_engine = create_async_engine(url, echo=False)
    return _async_engine


def get_async_session_maker():
    global _AsyncSession
    if _AsyncSession is None:
        _AsyncSession = async_sessionmaker(
            get_async_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSession


async def init_db() -> None:
    """Create all tables. Called on application startup."""
    async with get_async_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
