from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Iterator, Optional

from slack_sdk.oauth.installation_store.async_installation_store import AsyncInstallationStore
from slack_sdk.oauth.installation_store.models import Bot, Installation
from sqlalchemy import Engine, create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from core.config.base import get_settings, json_serializer_for_sqlalchemy
from core.db.models.slack import SlackInstallation

logger = logging.getLogger(__name__)


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _timestamp_to_datetime(value: Optional[float]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def _datetime_to_timestamp(value: Optional[datetime]) -> float:
    if value is None:
        return datetime.now(timezone.utc).timestamp()
    return value.timestamp()


def _serialize_scopes(scopes: Optional[Any]) -> str:
    if scopes is None:
        return ""
    if isinstance(scopes, str):
        return scopes
    return ",".join(list(scopes))


def _serialize_installation(
    installation: Installation, agent_system_name: str
) -> dict[str, Any]:
    custom_values: dict[str, Any] = dict(installation.custom_values or {})
    custom_values.setdefault("agent_system_name", agent_system_name)

    return {
        "app_id": installation.app_id,
        "enterprise_id": installation.enterprise_id,
        "enterprise_name": installation.enterprise_name,
        "enterprise_url": installation.enterprise_url,
        "team_id": installation.team_id,
        "team_name": installation.team_name,
        "bot_token": installation.bot_token,
        "bot_id": installation.bot_id,
        "bot_user_id": installation.bot_user_id,
        "bot_scopes": _serialize_scopes(installation.bot_scopes),
        "bot_refresh_token": installation.bot_refresh_token,
        "bot_token_expires_at": installation.bot_token_expires_at,
        "user_id": installation.user_id,
        "user_token": installation.user_token,
        "user_scopes": _serialize_scopes(installation.user_scopes),
        "user_refresh_token": installation.user_refresh_token,
        "user_token_expires_at": installation.user_token_expires_at,
        "incoming_webhook_url": installation.incoming_webhook_url,
        "incoming_webhook_channel": installation.incoming_webhook_channel,
        "incoming_webhook_channel_id": installation.incoming_webhook_channel_id,
        "incoming_webhook_configuration_url": installation.incoming_webhook_configuration_url,
        "is_enterprise_install": bool(installation.is_enterprise_install),
        "token_type": installation.token_type,
        "installed_at": installation.installed_at,
        "custom_values": custom_values,
    }


def _serialize_bot(bot: Optional[Bot], agent_system_name: str) -> Optional[dict[str, Any]]:
    if bot is None:
        return None

    custom_values: dict[str, Any] = dict(bot.custom_values or {})
    custom_values.setdefault("agent_system_name", agent_system_name)

    return {
        "app_id": bot.app_id,
        "enterprise_id": bot.enterprise_id,
        "enterprise_name": bot.enterprise_name,
        "team_id": bot.team_id,
        "team_name": bot.team_name,
        "bot_token": bot.bot_token,
        "bot_id": bot.bot_id,
        "bot_user_id": bot.bot_user_id,
        "bot_scopes": _serialize_scopes(bot.bot_scopes),
        "bot_refresh_token": bot.bot_refresh_token,
        "bot_token_expires_at": bot.bot_token_expires_at,
        "is_enterprise_install": bool(bot.is_enterprise_install),
        "installed_at": bot.installed_at,
        "custom_values": custom_values,
    }


def _deserialize_installation(record: SlackInstallation) -> Optional[Installation]:
    payload: dict[str, Any] = dict(record.installation_data or {})
    user_id = payload.get("user_id") or record.user_id
    if not user_id:
        logger.warning("Slack installation record %s missing user_id", record.id)
        return None

    installed_at = payload.get("installed_at")
    if installed_at is None and record.installed_at is not None:
        installed_at = _datetime_to_timestamp(record.installed_at)

    try:
        return Installation(
            app_id=payload.get("app_id") or record.app_id,
            enterprise_id=payload.get("enterprise_id") or record.enterprise_id,
            enterprise_name=payload.get("enterprise_name"),
            enterprise_url=payload.get("enterprise_url"),
            team_id=payload.get("team_id") or record.team_id,
            team_name=payload.get("team_name"),
            bot_token=payload.get("bot_token"),
            bot_id=payload.get("bot_id"),
            bot_user_id=payload.get("bot_user_id"),
            bot_scopes=payload.get("bot_scopes"),
            bot_refresh_token=payload.get("bot_refresh_token"),
            bot_token_expires_at=payload.get("bot_token_expires_at"),
            user_id=user_id,
            user_token=payload.get("user_token"),
            user_scopes=payload.get("user_scopes"),
            user_refresh_token=payload.get("user_refresh_token"),
            user_token_expires_at=payload.get("user_token_expires_at"),
            incoming_webhook_url=payload.get("incoming_webhook_url"),
            incoming_webhook_channel=payload.get("incoming_webhook_channel"),
            incoming_webhook_channel_id=payload.get("incoming_webhook_channel_id"),
            incoming_webhook_configuration_url=payload.get("incoming_webhook_configuration_url"),
            is_enterprise_install=payload.get("is_enterprise_install", record.is_enterprise_install),
            token_type=payload.get("token_type"),
            installed_at=installed_at,
            custom_values=payload.get("custom_values") or {},
        )
    except Exception:
        logger.exception("Failed to deserialize Slack installation from record %s", record.id)
        return None


def _deserialize_bot(record: SlackInstallation) -> Optional[Bot]:
    payload: dict[str, Any] = dict(record.bot_data or record.installation_data or {})
    bot_token = payload.get("bot_token")
    bot_id = payload.get("bot_id")
    bot_user_id = payload.get("bot_user_id")

    if not bot_token or not bot_id or not bot_user_id:
        return None

    installed_at = payload.get("installed_at")
    if installed_at is None and record.installed_at is not None:
        installed_at = _datetime_to_timestamp(record.installed_at)

    try:
        return Bot(
            app_id=payload.get("app_id") or record.app_id,
            enterprise_id=payload.get("enterprise_id") or record.enterprise_id,
            enterprise_name=payload.get("enterprise_name"),
            team_id=payload.get("team_id") or record.team_id,
            team_name=payload.get("team_name"),
            bot_token=bot_token,
            bot_id=bot_id,
            bot_user_id=bot_user_id,
            bot_scopes=payload.get("bot_scopes"),
            bot_refresh_token=payload.get("bot_refresh_token"),
            bot_token_expires_at=payload.get("bot_token_expires_at"),
            is_enterprise_install=payload.get("is_enterprise_install", record.is_enterprise_install),
            installed_at=installed_at,
            custom_values=payload.get("custom_values") or {},
        )
    except Exception:
        logger.exception("Failed to deserialize Slack bot from record %s", record.id)
        return None


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


class SlackInstallationStore(AsyncInstallationStore):
    """Persistent installation store backed by PostgreSQL."""

    def __init__(
        self,
        *,
        agent_system_name: str,
        client_id: str,
        app_id: Optional[str] = None,
        engine: Optional[Engine] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._agent_system_name = agent_system_name
        self._client_id = client_id
        self._app_id = app_id
        self._logger = logger or logging.getLogger(__name__)

        self._engine = engine or _get_sync_engine()
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

        # Ensure the backing table exists for environments where migrations haven't run yet.
        try:
            SlackInstallation.__table__.create(bind=self._engine, checkfirst=True)
        except Exception:  # pragma: no cover - defensive
            self.logger.exception("Failed to ensure slack_installations table exists")
            raise

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

    def _base_query(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        session: Session,
    ):
        query = select(SlackInstallation).where(
            SlackInstallation.client_id == self._client_id,
            SlackInstallation.agent_system_name == self._agent_system_name,
        )
        if enterprise_id is None:
            query = query.where(SlackInstallation.enterprise_id.is_(None))
        else:
            query = query.where(SlackInstallation.enterprise_id == enterprise_id)

        if team_id is None:
            query = query.where(SlackInstallation.team_id.is_(None))
        else:
            query = query.where(SlackInstallation.team_id == team_id)

        return query.order_by(
            SlackInstallation.installed_at.desc(),
            SlackInstallation.created_at.desc(),
        )

    def _save_sync(self, installation: Installation) -> None:
        enterprise_id = _normalize(installation.enterprise_id)
        team_id = _normalize(installation.team_id)
        user_id = installation.user_id

        try:
            bot = installation.to_bot()
        except Exception:
            bot = None

        payload = _serialize_installation(installation, self._agent_system_name)
        bot_payload = _serialize_bot(bot, self._agent_system_name)

        with self._session() as session:
            query = self._base_query(
                enterprise_id=enterprise_id,
                team_id=team_id,
                session=session,
            ).where(SlackInstallation.user_id == user_id)

            record = session.execute(query).scalars().first()
            installed_at = _timestamp_to_datetime(installation.installed_at)

            if record is None:
                record = SlackInstallation(
                    agent_system_name=self._agent_system_name,
                    client_id=self._client_id,
                    app_id=installation.app_id or self._app_id,
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    user_id=user_id,
                    is_enterprise_install=bool(installation.is_enterprise_install),
                    installed_at=installed_at,
                    installation_data=payload,
                    bot_data=bot_payload,
                )
                session.add(record)
            else:
                record.app_id = installation.app_id or self._app_id or record.app_id
                record.enterprise_id = enterprise_id
                record.team_id = team_id
                record.user_id = user_id
                record.is_enterprise_install = bool(installation.is_enterprise_install)
                record.installed_at = installed_at
                record.installation_data = payload
                record.bot_data = bot_payload

    def _save_bot_sync(self, bot: Bot) -> None:
        enterprise_id = _normalize(bot.enterprise_id)
        team_id = _normalize(bot.team_id)
        bot_payload = _serialize_bot(bot, self._agent_system_name)

        if bot_payload is None:
            return

        with self._session() as session:
            query = self._base_query(
                enterprise_id=enterprise_id,
                team_id=team_id,
                session=session,
            )
            record = session.execute(query).scalars().first()

            if record is None:
                self.logger.warning(
                    "No Slack installation found for bot update (client_id=%s, enterprise_id=%s, team_id=%s)",
                    self._client_id,
                    enterprise_id,
                    team_id,
                )
                return

            record.app_id = bot.app_id or self._app_id or record.app_id
            record.is_enterprise_install = bool(bot.is_enterprise_install)
            record.installed_at = _timestamp_to_datetime(bot.installed_at)
            record.bot_data = bot_payload

    def _find_bot_sync(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        normalized_enterprise = _normalize(enterprise_id)
        normalized_team = _normalize(team_id)

        with self._session() as session:
            query = self._base_query(
                enterprise_id=normalized_enterprise,
                team_id=normalized_team,
                session=session,
            )
            record = session.execute(query).scalars().first()
            if record is None:
                return None

            bot = _deserialize_bot(record)
            if bot is None:
                return None

            if is_enterprise_install is not None and bot.is_enterprise_install != bool(is_enterprise_install):
                return None

            return bot

    def _find_installation_sync(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        normalized_enterprise = _normalize(enterprise_id)
        normalized_team = _normalize(team_id)
        normalized_user = user_id

        with self._session() as session:
            query = self._base_query(
                enterprise_id=normalized_enterprise,
                team_id=normalized_team,
                session=session,
            )
            if normalized_user:
                query = query.where(SlackInstallation.user_id == normalized_user)

            record = session.execute(query).scalars().first()
            if record is None:
                return None

            installation = _deserialize_installation(record)
            if installation is None:
                return None

            if is_enterprise_install is not None and installation.is_enterprise_install != bool(is_enterprise_install):
                return None

            return installation

    def _delete_bot_sync(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        normalized_enterprise = _normalize(enterprise_id)
        normalized_team = _normalize(team_id)

        with self._session() as session:
            query = self._base_query(
                enterprise_id=normalized_enterprise,
                team_id=normalized_team,
                session=session,
            )
            records = session.execute(query).scalars().all()

            for record in records:
                record.bot_data = None

    def _delete_installation_sync(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        normalized_enterprise = _normalize(enterprise_id)
        normalized_team = _normalize(team_id)

        with self._session() as session:
            query = self._base_query(
                enterprise_id=normalized_enterprise,
                team_id=normalized_team,
                session=session,
            )
            if user_id:
                query = query.where(SlackInstallation.user_id == user_id)

            records = session.execute(query).scalars().all()
            for record in records:
                session.delete(record)

    def _delete_all_sync(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ):
        normalized_enterprise = _normalize(enterprise_id)
        normalized_team = _normalize(team_id)

        with self._session() as session:
            stmt = (
                delete(SlackInstallation)
                .where(
                    SlackInstallation.client_id == self._client_id,
                    SlackInstallation.agent_system_name == self._agent_system_name,
                )
            )
            if normalized_enterprise is None:
                stmt = stmt.where(SlackInstallation.enterprise_id.is_(None))
            else:
                stmt = stmt.where(SlackInstallation.enterprise_id == normalized_enterprise)

            if normalized_team is None:
                stmt = stmt.where(SlackInstallation.team_id.is_(None))
            else:
                stmt = stmt.where(SlackInstallation.team_id == normalized_team)

            session.execute(stmt)

    # ------------------------------------------------------------------
    # AsyncInstallationStore interface
    # ------------------------------------------------------------------

    def save(self, installation: Installation) -> None:
        self._save_sync(installation)

    async def async_save(self, installation: Installation):
        await asyncio.to_thread(self._save_sync, installation)

    def save_bot(self, bot: Bot) -> None:
        self._save_bot_sync(bot)

    async def async_save_bot(self, bot: Bot):
        await asyncio.to_thread(self._save_bot_sync, bot)

    async def async_find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        return await asyncio.to_thread(
            self._find_bot_sync,
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=is_enterprise_install,
        )

    async def async_find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        return await asyncio.to_thread(
            self._find_installation_sync,
            enterprise_id=enterprise_id,
            team_id=team_id,
            user_id=user_id,
            is_enterprise_install=is_enterprise_install,
        )

    def delete_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        self._delete_bot_sync(enterprise_id=enterprise_id, team_id=team_id)

    async def async_delete_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        await asyncio.to_thread(
            self._delete_bot_sync,
            enterprise_id=enterprise_id,
            team_id=team_id,
        )

    def delete_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        self._delete_installation_sync(
            enterprise_id=enterprise_id,
            team_id=team_id,
            user_id=user_id,
        )

    async def async_delete_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        await asyncio.to_thread(
            self._delete_installation_sync,
            enterprise_id=enterprise_id,
            team_id=team_id,
            user_id=user_id,
        )

    def delete_all(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        self._delete_all_sync(enterprise_id=enterprise_id, team_id=team_id)

    async def async_delete_all(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ):
        await asyncio.to_thread(
            self._delete_all_sync,
            enterprise_id=enterprise_id,
            team_id=team_id,
        )
