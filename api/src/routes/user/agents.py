from logging import getLogger
from typing import Any, Dict

from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from litestar import Controller, Request, post
from litestar.exceptions import ValidationException
from litestar.params import Body
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from microsoft_agents.hosting.aiohttp import jwt_authorization_middleware, start_agent_process
from services.agents.teams.runtime_cache import TeamsRuntimeCache

from api.tags import TagNames
from .agents_utils.aiohttp_like import AiohttpLikeRequest
from .agents_utils.jwt_utils import pick_audience, read_jwt_payload_noverify


logger = getLogger(__name__)


class UserAgentsController(Controller):
    path = "/agents"
    tags = [TagNames.UserAgentsMessages]

    @post(
        "/teams/messages",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="Messaging endpoint for Azure Bot Service (Teams integration)",
        description=(
            "Azure Bot Service messaging endpoint."
        ),
    )
    async def create_message(self, request: Request, data: Dict[str, Any] | None = Body()) -> Response:
        def _error(status: int, message: str) -> Response:
            return Response(status_code=status, content={"detail": message}, media_type="application/json")

        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return _error(HTTP_401_UNAUTHORIZED, "Missing Bearer token")

        token = auth_header.split(" ", 1)[1].strip()
        try:
            jwt_payload = read_jwt_payload_noverify(token)
        except ValidationException:
            return _error(HTTP_400_BAD_REQUEST, "Invalid JWT")

        audience = pick_audience(jwt_payload)
        if not audience:
            return _error(HTTP_400_BAD_REQUEST, "Invalid audience/appid")

        try:
            teams_runtime_cache = getattr(request.app.state, "teams_runtime_cache", None)
            if teams_runtime_cache is None:
                teams_runtime_cache = TeamsRuntimeCache()
                request.app.state.teams_runtime_cache = teams_runtime_cache
            team_agent = await teams_runtime_cache.get_or_create(audience)
        except Exception:
            logger.exception("TeamsRuntimeCache get_or_create failed for audience=%s", audience)
            return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Teams runtime unavailable")

        if data is None:
            data = {}

        fake_request = AiohttpLikeRequest(
            method="POST",
            url=str(request.url),
            headers=dict(request.headers),
            json_body=data,
            app_state={"agent_configuration": team_agent.validation_config},
            auth_header=auth_header,
        )

        aiohttp_response = None
        try:
            async def _next(req: AiohttpLikeRequest):
                return await start_agent_process(req, team_agent.agent_app, team_agent.adapter)

            aiohttp_response = await jwt_authorization_middleware(fake_request, _next)
        except (ExpiredSignatureError, InvalidTokenError):
            return _error(HTTP_401_UNAUTHORIZED, "Unauthorized")
        except Exception:
            logger.exception("Error while processing activity for audience %s", audience)
            return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Internal error while processing activity")
    
        if aiohttp_response is None:
            return Response(status_code=HTTP_200_OK)

        status = getattr(aiohttp_response, "status", HTTP_200_OK)
        headers = {str(key): str(value) for key, value in getattr(aiohttp_response, "headers", {}).items()}

        response_body = getattr(aiohttp_response, "body", b"")
        if isinstance(response_body, (bytes, bytearray)):
            content: Any = bytes(response_body)
        elif response_body is None:
            content = ""
        else:
            content = response_body

        return Response(status_code=status, content=content, headers=headers)
