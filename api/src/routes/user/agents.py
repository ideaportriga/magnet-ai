import html
import re
from http.cookies import SimpleCookie
from logging import getLogger
from typing import Any, Dict, Iterable, List
from urllib.parse import parse_qsl, quote, urlencode

from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from litestar import Controller, Request, get, post
from litestar.exceptions import ValidationException
from litestar.params import Body
from litestar.response import Response
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from microsoft_agents.hosting.aiohttp import jwt_authorization_middleware, start_agent_process
from slack_bolt.request import BoltRequest
from slack_bolt.response import BoltResponse

from api.tags import TagNames

from services.agents.teams.runtime_cache import TeamsRuntimeCache
from services.agents.slack.runtime_cache import SlackRuntimeCache
from services.agents.slack.runtime import SlackRuntime
from services.agents.slack.state_store import SlackOAuthStateStore
from .agents_utils.aiohttp_like import AiohttpLikeRequest
from .agents_utils.jwt_utils import pick_audience, read_jwt_payload_noverify

logger = getLogger(__name__)

async def _get_slack_runtime_cache(app: Any) -> SlackRuntimeCache:
    slack_runtime_cache: SlackRuntimeCache | None = getattr(app.state, "slack_runtime_cache", None)
    if slack_runtime_cache is None:
        slack_runtime_cache = SlackRuntimeCache()
        app.state.slack_runtime_cache = slack_runtime_cache
        await slack_runtime_cache.load()
    return slack_runtime_cache


def _error(status: int, message: str) -> Response:
    return Response(status_code=status, content={"detail": message}, media_type="application/json")


_DEFAULT_BOLT_CONTENT = object()


def _request_headers(request: Request) -> Dict[str, str]:
    return {str(k): str(v) for k, v in request.headers.items()}


def _litestar_response_from_bolt(
    bolt_response: BoltResponse,
    *,
    content: Any = _DEFAULT_BOLT_CONTENT,
    status_code: int | None = None,
    media_type: str | None = None,
    drop_headers: Iterable[str] | None = None,
    default_cookie_path: str | None = None,
    include_cookies: bool = True,
) -> Response:
    """Convert a BoltResponse into a Litestar Response"""
    headers: Dict[str, str] = {}
    cookie_morsels: list[SimpleCookie] = []
    excluded = {name.lower() for name in drop_headers} if drop_headers else set()

    if bolt_response.headers:
        for name, values in bolt_response.headers.items():
            if not values:
                continue
            lower_name = name.lower()
            if lower_name == "set-cookie":
                if not include_cookies:
                    continue
                for value in values:
                    cookie = SimpleCookie()
                    try:
                        cookie.load(value)
                    except Exception:
                        continue
                    cookie_morsels.append(cookie)
            elif lower_name in excluded:
                continue
            else:
                headers[name] = ", ".join(str(v) for v in values)

    response = Response(
        status_code=status_code or bolt_response.status,
        content=bolt_response.body if content is _DEFAULT_BOLT_CONTENT else content,
        headers=headers,
        media_type=media_type,
    )

    default_path = default_cookie_path or "/"
    if include_cookies:
        for cookie in cookie_morsels:
            for morsel in cookie.values():
                max_age = int(morsel["max-age"]) if morsel["max-age"] else None
                expires = morsel["expires"] or None
                domain = morsel["domain"] or None
                path = default_path if default_cookie_path else (morsel["path"] or default_path)
                secure = "secure" in morsel.keys()
                httponly = "httponly" in morsel.keys()
                samesite_value = morsel["samesite"] or None
                samesite = samesite_value.lower() if isinstance(samesite_value, str) and samesite_value else None

                response.set_cookie(
                    key=morsel.key,
                    value=morsel.value,
                    max_age=max_age,
                    expires=expires,
                    path=path,
                    domain=domain,
                    secure=secure,
                    httponly=httponly,
                    samesite=samesite,
                )

    return response


def _extract_urls_from_body(bolt_response: BoltResponse) -> tuple[str | None, str | None]:
    """Attempt to find browser/deep links inside Bolt's HTML body."""
    body = bolt_response.body or ""
    if isinstance(body, (bytes, bytearray)):
        try:
            body = body.decode("utf-8", errors="ignore")
        except Exception:
            body = ""
    if not isinstance(body, str):
        body = str(body)

    browser_match = re.search(r"https://app\.slack\.com/[^\s\"'>]+", body)
    browser_url = browser_match.group(0) if browser_match else None

    deep_link_match = re.search(r"slack://[^\s\"'>]+", body)
    deep_link_url = deep_link_match.group(0) if deep_link_match else None

    return browser_url, deep_link_url


def _bolt_body_to_text(body: Any) -> str:
    if isinstance(body, (bytes, bytearray)):
        try:
            return body.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    if isinstance(body, str):
        return body
    return str(body)


def _bolt_response_oauth_result(
    bolt_response: BoltResponse,
    query_params: dict[str, str] | None = None,
) -> str:
    status = bolt_response.status or 200
    if status >= 400:
        return "error"

    qp = {k.lower(): v for k, v in (query_params or {}).items()}
    if "error" in qp:
        return "error"
    if qp.get("reason"):
        return "error"

    loc_values = None
    if bolt_response.headers:
        for k, vals in bolt_response.headers.items():
            if k.lower() == "location" and vals:
                loc_values = vals
                break
    if loc_values:
        return "success"

    body_text = _bolt_body_to_text(bolt_response.body).lower()
    if "error" in body_text and "slack" in body_text:
        return "error"

    return "success"


def _render_oauth_success_page(
    *,
    agent_name: str | None,
    open_app_url: str | None,
    open_browser_url: str | None,
) -> str:
    open_app_url = open_app_url or "slack://open"
    open_browser_url = open_browser_url or "https://app.slack.com/client"
    safe_agent = html.escape(agent_name or "Slack App")
    open_app_markup = (
        f'<a class="action-button action-button--primary" href="{html.escape(open_app_url, quote=True)}">Open Slack App</a>'
        if open_app_url
        else ""
    )
    open_browser_markup = (
        f'<a class="action-button action-button--secondary" href="{html.escape(open_browser_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open in Browser</a>'
        if open_browser_url
        else ""
    )

    buttons_markup = "".join(filter(None, [open_app_markup, open_browser_markup])) or "<p>You're all set! You can now open Slack to start using the app.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{safe_agent} Installed • Magnet AI</title>
    <style>
      body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 40px; background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
      .card {{ background-color: rgba(15, 23, 42, 0.85); border-radius: 20px; padding: 40px; max-width: 520px; width: 100%; box-shadow: 0 25px 50px rgba(15, 23, 42, 0.45); text-align: center; }}
      p {{ font-size: 16px; margin-bottom: 28px; line-height: 1.6; color: #cbd5f5; }}
      .buttons {{ display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; }}
      .action-button {{ display: inline-flex; justify-content: center; align-items: center; padding: 14px 28px; border-radius: 999px; text-decoration: none; font-weight: 600; transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease; }}
      .action-button {{ background-color: rgba(248, 250, 252, 0.12); color: #f8fafc; }}
      .action-button:hover {{ background-color: rgba(248, 250, 252, 0.2); transform: translateY(-2px); }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>{safe_agent} has been connected to Slack</h1>
      <div class="buttons">
        {buttons_markup}
      </div>
    </div>
  </body>
</html>"""


async def _handle_slack_bolt_request(request: Request, *, error_message: str) -> Response:
    try:
        slack_runtime_cache = await _get_slack_runtime_cache(request.app)
        raw_body = await request.body()
        headers = _request_headers(request)

        slack_agent: SlackRuntime | None = slack_runtime_cache.find(raw_body, headers)
        if slack_agent is None:
            return _error(HTTP_400_BAD_REQUEST, "No Slack agent found")

        body_text = raw_body.decode("utf-8", errors="replace")
        bolt_request = BoltRequest(
            body=body_text,
            query=request.url.query or None,
            headers=headers,
        )
        bolt_response = slack_agent.handler.app.dispatch(bolt_request)
    except Exception:
        logger.exception(error_message)
        return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Slack runtime unavailable")

    return _litestar_response_from_bolt(bolt_response, include_cookies=False)


class UserAgentsController(Controller):
    path = "/agents"
    tags = [TagNames.UserAgentsMessages]

    @post(
        "/teams/messages",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="Messaging endpoint for Azure Bot Service (Teams integration)",
        description="Azure Bot Service messaging endpoint.",
    )
    async def handle_teams_message(self, request: Request, data: Dict[str, Any] | None = Body()) -> Response:
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


    @post(
        "/slack/events",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="Messaging endpoint for Slack Events",
        description="The endpoint for Slack events (specifcied in the Slack app manifest).",
    )
    async def handle_slack_event(self, request: Request, data: Dict[str, Any] | None = Body()) -> Response:
        return await _handle_slack_bolt_request(
            request,
            error_message="Slack runtime failed to handle request",
        )


    @post(
        "/slack/interactive",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="Interactivity endpoint for Slack (block_actions, view_submission, shortcuts)",
        description=(
            "The endpoint configured under Slack 'Interactivity & Shortcuts' for interactive components."
        ),
    )
    async def handle_slack_interactive(self, request: Request, data: Dict[str, Any] | None = Body()) -> Response:
        return await _handle_slack_bolt_request(
            request,
            error_message="Slack runtime failed to handle interactivity request",
        )


    @get(
        "/slack/install",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="Install endpoint for Slack Apps",
        description="The endpoint for Slack installation (opened from admin ui).",
    )
    async def handle_slack_install(self, request: Request) -> Response:

        try:
            slack_runtime_cache = await _get_slack_runtime_cache(request.app)
        except Exception:
            logger.exception("Failed to initialize Slack runtime cache for install endpoint")
            return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Slack runtime unavailable")

        oauth_agents = [runtime for runtime in slack_runtime_cache.all() if runtime.install_path]
        if not oauth_agents:
            return _error(HTTP_404_NOT_FOUND, "No Slack agents configured for installation")

        query_params = dict(parse_qsl(request.url.query or "", keep_blank_values=True))
        target_agent_system_name = query_params.pop("agent", None)

        if not target_agent_system_name:
            return _error(HTTP_400_BAD_REQUEST, "No Slack agent system name specified for installation")

        selected_agent = next((agent for agent in oauth_agents if agent.agent_system_name == target_agent_system_name), None)
        if selected_agent is None:
            return _error(HTTP_404_NOT_FOUND, f"Slack agent '{target_agent_system_name}' not found")

        oauth_flow = getattr(selected_agent.handler.app, "oauth_flow", None)
        if oauth_flow is None:
            return _error(HTTP_400_BAD_REQUEST, "Slack agent does not support OAuth installation")

        sanitized_query = urlencode(query_params, doseq=True)
        headers = _request_headers(request)

        bolt_request = BoltRequest(
            body="",
            query=sanitized_query or None,
            headers=headers,
        )

        try:
            bolt_response = oauth_flow.handle_installation(bolt_request)
        except Exception:
            logger.exception("Slack OAuth installation failed for agent '%s'", selected_agent.name)
            return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Slack OAuth installation failed")

        return _litestar_response_from_bolt(
            bolt_response,
            content=bolt_response.body or "",
            default_cookie_path=selected_agent.redirect_uri_path or "/", # request.url.path
        )


    @get(
        "/slack/oauth_redirect",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        summary="OAuth callback endpoint for Slack Apps",
        description="Completes the Slack OAuth installation flow.",
    )
    async def handle_slack_oauth_redirect(self, request: Request) -> Response:

        try:
            slack_runtime_cache = await _get_slack_runtime_cache(request.app)
        except Exception:
            logger.exception("Failed to initialize Slack runtime cache for OAuth callback endpoint")
            return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Slack runtime unavailable")

        oauth_agents = [runtime for runtime in slack_runtime_cache.all() if runtime.install_path]
        if not oauth_agents:
            return _error(HTTP_404_NOT_FOUND, "No Slack agents configured for installation")

        query_string = request.url.query or ""
        query_params = dict(parse_qsl(query_string, keep_blank_values=True))
        state_value = query_params.get("state") or query_params.get("agent")

        headers = _request_headers(request)

        runtime: SlackRuntime | None = None
        if state_value:
            lookup = SlackOAuthStateStore.lookup_agent_by_state(state_value)
            if lookup is None:
                return _error(HTTP_500_INTERNAL_SERVER_ERROR, "No state found for OAuth callback")
            
            agent_system_name = lookup[0]
            runtime = next((agent for agent in oauth_agents if agent.agent_system_name == agent_system_name), None)
            if runtime is None:
                logger.warning(
                    "Slack OAuth state mapped to unknown agent '%s'. state=%s",
                    agent_system_name,
                    state_value,
                )
                return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Could not determine Slack agent for OAuth callback")

            oauth_flow = getattr(runtime.handler.app, "oauth_flow", None)
            if oauth_flow is None:
                return _error(HTTP_500_INTERNAL_SERVER_ERROR, "OAuth flow is not configured for this Slack runtime")

            bolt_request = BoltRequest(
                body="",
                query=query_string or None,
                headers=headers,
            )

            try:
                bolt_response = oauth_flow.handle_callback(bolt_request)

                oaut_result = _bolt_response_oauth_result(bolt_response, query_params)

                if oaut_result == "error":
                    return _litestar_response_from_bolt(
                        bolt_response,
                        content=bolt_response.body or "",
                        status_code=bolt_response.status or HTTP_400_BAD_REQUEST,
                        media_type="text/html",
                    )

                body_browser_url, body_deep_link = _extract_urls_from_body(bolt_response)
                html_body = _render_oauth_success_page(
                    agent_name=runtime.name or runtime.agent_system_name,
                    open_app_url=body_deep_link,
                    open_browser_url=body_browser_url,
                )
                return _litestar_response_from_bolt(
                    bolt_response,
                    content=html_body,
                    status_code=HTTP_200_OK,
                    media_type="text/html",
                    drop_headers={"location"},
                )
            except Exception:
                logger.exception("Slack OAuth callback failed during token exchange/processing")
                return _error(HTTP_500_INTERNAL_SERVER_ERROR, "Slack OAuth callback failed")
