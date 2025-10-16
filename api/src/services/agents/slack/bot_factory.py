import logging
from dataclasses import dataclass
from typing import Sequence

from slack_bolt import App
from slack_bolt.adapter.asgi import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.signature import SignatureVerifier
from sqlalchemy import text

from core.config.app import alchemy

from .default_handlers import attach_default_handlers


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlackBot:
    name: str
    handler: SlackRequestHandler
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
) -> OAuthSettings | None:

    if not client_id or not client_secret:
        return None

    return OAuthSettings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        user_scopes=None,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
    )


def _build_bot_from_db(
    *,
    name: str,
    token: str | None,
    signing_secret: str,
    client_id: str | None,
    client_secret: str | None,
    scopes: str | None,
) -> SlackBot:
    oauth_settings = _create_oauth_settings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=_parse_scopes(scopes),
    )
    logger.debug("Creating Slack bot '%s'", name)
    bolt_app = App(
        token=token,
        signing_secret=signing_secret,
        oauth_settings=oauth_settings,
    )
    attach_default_handlers(bolt_app)
    handler = SlackRequestHandler(bolt_app)
    verifier = SignatureVerifier(signing_secret=signing_secret)
    install_path = oauth_settings.install_path if oauth_settings else None
    redirect_uri_path = oauth_settings.redirect_uri_path if oauth_settings else None
    return SlackBot(
        name=name,
        handler=handler,
        verifier=verifier,
        install_path=install_path,
        redirect_uri_path=redirect_uri_path,
    )


async def discover_bots_from_db() -> Sequence[SlackBot]:

    sql = text(
        """
        SELECT
            COALESCE(elem->'value'->'credentials'->>'name', a.name, a.system_name) AS name,
            elem->'value'->'secrets_encrypted'->'slack'->>'token' AS token,
            elem->'value'->'secrets_encrypted'->'slack'->>'signing_secret' AS signing_secret,
            elem->'value'->'credentials'->'slack'->>'client_id' AS client_id,
            elem->'value'->'secrets_encrypted'->'slack'->>'client_secret' AS client_secret,
            elem->'value'->'credentials'->'slack'->>'scopes' AS scopes
        FROM agents a,
             jsonb_array_elements(a.variants) AS elem
        WHERE 
          COALESCE(elem->'value'->'secrets_encrypted'->'slack'->>'signing_secret', '') <> ''
        """
    )

    async with alchemy.get_session() as session:
        result = await session.execute(sql)
        rows = result.mappings().all()

    bots: list[SlackBot] = []
    for row in rows:
        bots.append(
            _build_bot_from_db(
                name=row.get("name"),
                token=row.get("token"),
                signing_secret=row.get("signing_secret"),
                client_id=row.get("client_id"),
                client_secret=row.get("client_secret"),
                scopes=row.get("scopes"),
            )
        )

    logger.info("Initialized %d Slack bot(s): %s", len(bots), ", ".join(bot.name for bot in bots) or "<none>")
    return bots
