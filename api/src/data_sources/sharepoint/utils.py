import os
from logging import getLogger

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

from data_sources.common.utils import get_required_env_var
from data_sources.sharepoint.types import SharepointConfig, SharepointConfigWithCert

logger = getLogger(__name__)


def get_sharepoint_config() -> SharepointConfig | SharepointConfigWithCert:
    try:
        client_id = client_id = get_required_env_var("SHAREPOINT_CLIENT_ID")
        client_secret = os.environ.get("SHAREPOINT_CLIENT_SECRET", "")

        if client_secret:
            return SharepointConfig(client_id=client_id, client_secret=client_secret)

        sharepoint_config = SharepointConfigWithCert(
            tenant=get_required_env_var("SHAREPOINT_TENANT_ID"),
            client_id=client_id,
            thumbprint=get_required_env_var("SHAREPOINT_CLIENT_CERT_THUMBPRINT"),
            private_key=get_required_env_var(
                "SHAREPOINT_CLIENT_CERT_PRIVATE_KEY"
            ).replace("\\n", "\n"),
        )
        return sharepoint_config
    except Exception as err:
        raise ValueError("Sharepoint connection is misconfigured") from err


def get_sharepoint_context(
    sharepoint_site_url: str,
    sharepoint_config: SharepointConfig | SharepointConfigWithCert,
) -> ClientContext:
    auth_ctx = AuthenticationContext(url=sharepoint_site_url)
    if isinstance(sharepoint_config, SharepointConfigWithCert):
        auth_ctx.with_client_certificate(
            tenant=sharepoint_config.tenant,
            client_id=sharepoint_config.client_id,
            thumbprint=sharepoint_config.thumbprint,
            private_key=sharepoint_config.private_key,
        )
    else:
        auth_ctx.acquire_token_for_app(
            client_id=sharepoint_config.client_id,
            client_secret=sharepoint_config.client_secret,
        )

    ctx = ClientContext(sharepoint_site_url, auth_ctx)

    return ctx


def create_sharepoint_client(sharepoint_site_url: str) -> ClientContext:
    sharepoint_config = get_sharepoint_config()

    ctx = get_sharepoint_context(sharepoint_site_url, sharepoint_config)

    return ctx
