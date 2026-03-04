from __future__ import annotations

from dataclasses import dataclass

# Standard fields available on all Salesforce Knowledge Article View (__kav) objects.
# Used as defaults when the source config does not explicitly specify metadata_fields.
SALESFORCE_DEFAULT_METADATA_FIELDS: tuple[str, ...] = (
    "Title",
    "ArticleNumber",
    "UrlName",
    "Summary",
    "Language",
    "LastPublishedDate",
    "PublishStatus",
    "KnowledgeArticleId",
)


@dataclass(frozen=True)
class SalesforceRuntimeConfig:
    """Resolved Salesforce configuration for a single sync run."""

    # SOQL object type — must end with __kav (Knowledge Article View)
    object_api_name: str

    # Single Python format-string template, e.g. "question: {Question__c}\nanswer: {Answer__c}"
    content_template: str

    # system_name of the KS provider that holds Salesforce credentials
    provider_system_name: str

    # --- Username / password flow ---
    username: str = ""
    password: str = ""
    security_token: str = ""  # may be empty for IP-whitelisted orgs

    # --- OAuth 2.0 client credentials flow ---
    client_id: str = ""
    client_secret: str = ""

    # Salesforce instance domain segment: "login" (production) or "test" (sandbox)
    domain: str = "login"

    # Fields to SELECT for metadata discovery (in addition to Id, Title, CreatedDate, LastModifiedDate)
    metadata_fields: tuple[str, ...] = SALESFORCE_DEFAULT_METADATA_FIELDS

    @property
    def uses_client_credentials(self) -> bool:
        """True when OAuth 2.0 client credentials flow should be used."""
        return bool(self.client_id and self.client_secret)
