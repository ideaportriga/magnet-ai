from logging import getLogger

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

from core.config.base import get_knowledge_source_settings
from data_sources.sharepoint.types import SharepointConfig, SharepointConfigWithCert

logger = getLogger(__name__)


def get_sharepoint_config() -> SharepointConfig | SharepointConfigWithCert:
    settings = get_knowledge_source_settings()
    try:
        client_id = settings.SHAREPOINT_CLIENT_ID
        client_secret = settings.SHAREPOINT_CLIENT_SECRET

        if client_secret:
            return SharepointConfig(client_id=client_id, client_secret=client_secret)

        sharepoint_config = SharepointConfigWithCert(
            tenant=settings.SHAREPOINT_TENANT_ID,
            client_id=client_id,
            thumbprint=settings.SHAREPOINT_CLIENT_CERT_THUMBPRINT,
            private_key=settings.SHAREPOINT_CLIENT_CERT_PRIVATE_KEY.replace(
                "\\n", "\n"
            ),
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


def create_sharepoint_client_with_config(
    sharepoint_site_url: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    tenant: str | None = None,
    thumbprint: str | None = None,
    private_key: str | None = None,
) -> ClientContext:
    """Create SharePoint client with explicit configuration.

    This function allows passing credentials directly instead of reading from environment.
    Useful when credentials come from provider configuration in database.

    Args:
        sharepoint_site_url: SharePoint site URL
        client_id: Azure AD application client ID
        client_secret: Azure AD application client secret (for secret-based auth)
        tenant: Azure AD tenant ID (for certificate-based auth)
        thumbprint: Certificate thumbprint (for certificate-based auth)
        private_key: Certificate private key (for certificate-based auth)

    Returns:
        ClientContext instance

    Raises:
        ValueError: If required credentials are missing
    """
    # If no credentials provided, fall back to environment
    if not client_id:
        return create_sharepoint_client(sharepoint_site_url)

    # Build config based on provided credentials
    if client_secret:
        # Secret-based authentication
        sharepoint_config = SharepointConfig(
            client_id=client_id,
            client_secret=client_secret,
        )
    elif tenant and thumbprint and private_key:
        # Certificate-based authentication
        sharepoint_config = SharepointConfigWithCert(
            tenant=tenant,
            client_id=client_id,
            thumbprint=thumbprint,
            private_key=private_key.replace("\\n", "\n"),
        )
    else:
        raise ValueError(
            "Either client_secret or (tenant, thumbprint, private_key) must be provided"
        )

    ctx = get_sharepoint_context(sharepoint_site_url, sharepoint_config)
    return ctx
