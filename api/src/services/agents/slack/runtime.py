import logging
from dataclasses import dataclass
from typing import Sequence

from slack_bolt.adapter.asgi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.signature import SignatureVerifier
from sqlalchemy import text

from core.config.app import alchemy

from .handlers import attach_default_handlers
from .installation_store import SlackInstallationStore
from .state_store import SlackOAuthStateStore


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlackRuntime:
    name: str
    agent_system_name: str
    handler: AsyncSlackRequestHandler
    verifier: SignatureVerifier
    install_path: str | None = None
    redirect_uri_path: str | None = None


def _parse_scopes(value: str | None) -> list[str] | None:
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    scopes = [s for s in (part.strip() for part in value.split(",")) if s]

    return scopes or None


def _create_oauth_settings(
    *,
    client_id: str | None,
    client_secret: str | None,
    scopes: list[str] | None,
    agent_system_name: str,
    agent_display_name: str | None,
) -> AsyncOAuthSettings | None:

    if not client_id or not client_secret:
        return None

    installation_store = SlackInstallationStore(
        agent_system_name=agent_system_name,
        client_id=client_id,
    )
    state_store = SlackOAuthStateStore(
        agent_system_name=agent_system_name,
        agent_display_name=agent_display_name,
    )
    return AsyncOAuthSettings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        user_scopes=None,
        installation_store=installation_store,
        state_store=state_store,
        install_page_rendering_enabled=False,
        install_path="/api/user/agents/slack/install",
        redirect_uri_path="/api/user/agents/slack/oauth_redirect",
    )


def _build_bot_from_db(
    *,
    name: str,
    token: str | None,
    signing_secret: str,
    client_id: str | None,
    client_secret: str | None,
    scopes: str | None,
    agent_system_name: str,
) -> SlackRuntime:
    oauth_settings = _create_oauth_settings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=_parse_scopes(scopes),
        agent_system_name=agent_system_name,
        agent_display_name=name,
    )
    logger.debug("Creating Slack bot '%s' for agent '%s'", name, agent_system_name)
    if oauth_settings:
        bolt_app = AsyncApp(
            signing_secret=signing_secret,
            oauth_settings=oauth_settings,
        )
    else:
        bolt_app = AsyncApp(
            token=token,
            signing_secret=signing_secret,
        )
    attach_default_handlers(bolt_app)
    handler = AsyncSlackRequestHandler(bolt_app)
    verifier = SignatureVerifier(signing_secret=signing_secret)
    install_path = oauth_settings.install_path if oauth_settings else None
    redirect_uri_path = oauth_settings.redirect_uri_path if oauth_settings else None
    return SlackRuntime(
        name=name,
        agent_system_name=agent_system_name,
        handler=handler,
        verifier=verifier,
        install_path=install_path,
        redirect_uri_path=redirect_uri_path,
    )


async def discover_bots_from_db() -> Sequence[SlackRuntime]:
    sql = text(
        """
        SELECT
            a.name AS name, 
			a.system_name AS system_name,
            elem->'value'->'secrets_encrypted'->'slack'->>'token' AS token,
            elem->'value'->'credentials'->'slack'->>'client_id' AS client_id,
            elem->'value'->'secrets_encrypted'->'slack'->>'signing_secret' AS signing_secret,
            elem->'value'->'secrets_encrypted'->'slack'->>'client_secret' AS client_secret,
            elem->'value'->'credentials'->'slack'->>'scopes' AS scopes
        FROM agents a,
             jsonb_array_elements(a.variants) AS elem
        WHERE 
          COALESCE(elem->'value'->'credentials'->'slack'->>'client_id', '') <> ''
        """
    )

    async with alchemy.get_session() as session:
        result = await session.execute(sql)
        rows = result.mappings().all()

    bots: list[SlackRuntime] = []
    for row in rows:
        bots.append(
            _build_bot_from_db(
                name=row.get("name"),
                token=row.get("token"),
                signing_secret=row.get("signing_secret"),
                client_id=row.get("client_id"),
                client_secret=row.get("client_secret"),
                scopes=row.get("scopes"),
                agent_system_name=row.get('system_name'),
            )
        )

    logger.info("Initialized %d Slack bot(s): %s", len(bots), ", ".join(bot.name for bot in bots) or "<none>")
    return bots
