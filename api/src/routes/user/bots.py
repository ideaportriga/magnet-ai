from logging import getLogger
from litestar import Controller, Request, post
from litestar.params import Body
from litestar.response import Response
from typing import Any
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from microsoft_agents.hosting.aiohttp import jwt_authorization_middleware, start_agent_process

from api.tags import TagNames
from .jwt_utils import pick_audience, read_jwt_payload_noverify
from .aiohttp_like import AiohttpLikeRequest


logger = getLogger(__name__)


class UserBotsController(Controller):
    path = "/agents/messages"
    tags = [TagNames.UserAgentsMessages]

    @post(
        "",
        status_code=200,
        exclude_from_auth=True,
        summary="Messaging endpoint for Azure Bot Service (Teams integration)",
        description=(
            "Azure Bot Service messaging endpoint."
        ),
    )
    async def create_message(self, request: Request, data: dict = Body()) -> dict:
        # TOOD - REMOVE Log headers and body for debugging purposes
        try:
            logger.info("/api/user/agents/messages headers=%s", dict(request.headers))
        except Exception:
            logger.exception("Failed to log headers for /api/user/agents/messages")
        try:
            logger.info("/api/user/agents/messages body=%s", data)
        except Exception:
            logger.exception("Failed to log body for /api/user/agents/messages")

        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return Response(status_code=401, content="Missing Bearer token")

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = read_jwt_payload_noverify(token)
        except Exception:
            return Response(status_code=400, content="Invalid JWT")

        audience = pick_audience(payload)
        if not audience:
            return Response(status_code=400, content="Invalid audience/appid")

        try:
            runtime_cache = getattr(request.app.state, "bot_runtime_cache", None)
            if runtime_cache is None:
                return Response(status_code=500, content="Runtime cache unavailable")
            bot = await runtime_cache.get_or_create(audience)
            print("bot successfully created")
        except Exception:
            logger.exception("BotRuntimeCache get_or_create failed for audience=%s", audience)
            return Response(status_code=500, content="Bot runtime unavailable")

        try:
            body: dict[str, Any] = await request.json()
        except Exception:
            return Response(status_code=415, content="Invalid or missing JSON body")

        fake_request = AiohttpLikeRequest(
            method="POST",
            url=str(request.url),
            headers=dict(request.headers),
            json_body=body,
            app_state={"agent_configuration": bot.validation_config},
            auth_header=auth_header,
        )

        aiohttp_response = None
        try:
            async def _next(req: AiohttpLikeRequest):
                return await start_agent_process(req, bot.agent_app, bot.adapter)

            aiohttp_response = await jwt_authorization_middleware(fake_request, _next)
        except (ExpiredSignatureError, InvalidTokenError):
            return Response(status_code=401, content="Unauthorized")
        except Exception:
            logger.exception("Error while processing activity for audience %s", audience)
            return Response(status_code=500, content="Internal error while processing activity")
    
        if aiohttp_response is None:
            return Response(status_code=200)

        status = getattr(aiohttp_response, "status", 200)
        headers = {}
        for key, value in getattr(aiohttp_response, "headers", {}).items():
            headers[str(key)] = str(value)

        payload = getattr(aiohttp_response, "body", b"")
        content: str = ""
        if isinstance(payload, (bytes, bytearray)):
            try:
                content = payload.decode("utf-8")
            except UnicodeDecodeError:
                content = ""
        elif payload is None:
            content = ""
        else:
            content = str(payload)

        return Response(status_code=status, content=content, headers=headers)


