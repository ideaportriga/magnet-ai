from dataclasses import dataclass
from enum import StrEnum


@dataclass
class SharepointConfig:
    client_id: str
    client_secret: str


@dataclass
class SharepointConfigWithCert:
    # Azure AD tenant ID. Field was previously named `tenant`; renamed for
    # consistency with the access-control plan PR 3 naming.
    azure_tenant_id: str
    client_id: str
    thumbprint: str
    private_key: str


class SharePointRootFolder(StrEnum):
    PAGES = "SitePages"
    DOCUMENTS = "Shared Documents"


class SharePointFileExtension(StrEnum):
    PAGE = ".aspx"
    PDF = ".pdf"
    MP4 = ".mp4"
