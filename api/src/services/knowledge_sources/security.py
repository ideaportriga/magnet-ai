"""
Security-related constants and utilities for knowledge source providers.

This module defines security-critical fields that must only come from provider
configuration and should never be overridable from user-controlled knowledge
source configuration.
"""

# Security-critical fields that must ONLY come from provider configuration
# These fields are tied to authentication/authorization and should never be overridable
# from user-controlled knowledge source configuration to prevent:
# - Credential leakage to unintended endpoints
# - Unauthorized access using provider credentials
# - Security token/key exposure
#
# These fields are bound to the provider's endpoint and authentication context.
# Allowing them to be overridden from knowledge source config would create security
# vulnerabilities where an attacker could redirect authenticated requests to
# unauthorized endpoints or extract credentials.
PROVIDER_ONLY_FIELDS = frozenset(
    {
        # Endpoint configuration
        "endpoint",  # Provider endpoint URL (credentials are tied to this endpoint)
        # OAuth/Azure AD credentials
        "client_id",  # OAuth/Azure AD application client ID
        "client_secret",  # OAuth/Azure AD application client secret
        "tenant",  # Azure AD tenant ID
        # Certificate-based authentication
        "thumbprint",  # Certificate thumbprint
        "private_key",  # Certificate private key
        # Basic authentication
        "username",  # HTTP Basic auth username
        "password",  # HTTP Basic auth password
        # Token-based authentication
        "token",  # Generic API token
        "security_token",  # Salesforce security token
        "api_token",  # Generic API token (alternative naming)
        "api_key",  # API key
    }
)


def is_provider_only_field(field_name: str) -> bool:
    """
    Check if a field name is a security-critical provider-only field.

    Args:
        field_name: The field name to check

    Returns:
        True if the field should only come from provider configuration
    """
    return field_name in PROVIDER_ONLY_FIELDS


def filter_provider_only_fields(config: dict) -> dict:
    """
    Remove security-critical provider-only fields from a configuration dict.

    This is useful when processing user-provided configuration to ensure
    security-critical fields cannot be injected.

    Args:
        config: Configuration dictionary (typically from knowledge source)

    Returns:
        New dictionary with provider-only fields removed
    """
    return {k: v for k, v in config.items() if k not in PROVIDER_ONLY_FIELDS}
