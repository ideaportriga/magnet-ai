"""Database-backed OAuth state store for Slack installations."""

import logging
from contextlib import contextmanager
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional
from uuid import uuid4

from slack_sdk.oauth.state_store import OAuthStateStore
from sqlalchemy import Engine, create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from core.config.base import get_settings, json_serializer_for_sqlalchemy
from core.db.models.slack import SlackOAuthState

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_default_expiration(duration_seconds: int) -> datetime:
    return _utc_now() + timedelta(seconds=duration_seconds)


def _ensure_table(engine: Engine) -> None:
    SlackOAuthState.__table__.create(bind=engine, checkfirst=True)


@lru_cache(maxsize=1)
def _get_sync_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.db.sync_url,
        json_serializer=json_serializer_for_sqlalchemy,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.db.ECHO if isinstance(settings.db.ECHO, bool) else False,
    )


class SlackOAuthStateStore(OAuthStateStore):
    """Persistent OAuth state store using PostgreSQL."""

    def __init__(
        self,
        *,
        agent_system_name: str,
        agent_display_name: str,
        expiration_seconds: int = 600,
        engine: Optional[Engine] = None,
    ) -> None:
        self._agent_system_name = agent_system_name
        self._agent_display_name = agent_display_name
        self._expiration_seconds = expiration_seconds
        self._engine = engine or _get_sync_engine()
        _ensure_table(self._engine)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._logger = logging.getLogger(f"{__name__}.{agent_system_name}")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _cleanup_expired(self, session: Session) -> None:
        now = _utc_now()
        session.execute(
            delete(SlackOAuthState).where(SlackOAuthState.expires_at < now)
        )

    def issue(self, *args, **kwargs) -> str:  # type: ignore[override]
        state = str(uuid4())
        expires_at = _get_default_expiration(self._expiration_seconds)
        with self._session() as session:
            self._cleanup_expired(session)
            session.add(
                SlackOAuthState(
                    state_token=state,
                    agent_system_name=self._agent_system_name,
                    agent_display_name=self._agent_display_name,
                    expires_at=expires_at,
                )
            )
        return state

    def consume(self, state: str) -> bool:  # type: ignore[override]
        now = _utc_now()
        with self._session() as session:
            record = (
                session.execute(
                    select(SlackOAuthState).where(
                        SlackOAuthState.state_token == state
                    )
                )
                .scalars()
                .one_or_none()
            )
            if record is None:
                self.logger.warning("Slack OAuth state not found: %s", state)
                return False

            session.delete(record)
            valid = record.expires_at > now
            if not valid:
                self.logger.warning(
                    "Slack OAuth state expired before callback: %s (expired at %s)",
                    state,
                    record.expires_at,
                )
            return valid

    @classmethod
    def lookup_agent_by_state(cls, state: str) -> Optional[tuple[str, Optional[str]]]:
        engine = _get_sync_engine()
        _ensure_table(engine)
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
        with SessionFactory() as session:
            record = (
                session.execute(
                    select(SlackOAuthState).where(
                        SlackOAuthState.state_token == state
                    )
                )
                .scalars()
                .one_or_none()
            )
            if record is None:
                return None
            if record.expires_at <= _utc_now():
                session.delete(record)
                session.commit()
                return None
            return record.agent_system_name, record.agent_display_name
