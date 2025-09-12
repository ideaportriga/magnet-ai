from dataclasses import dataclass
from enum import StrEnum


@dataclass
class SharepointConfig:
    client_id: str
    client_secret: str


@dataclass
class SharepointConfigWithCert:
    tenant: str
    client_id: str
    thumbprint: str
    private_key: str


class DocumentSourceType(StrEnum):
    PDF = "pdf"
    VIDEO = "video"
    SITE_PAGE = "site_page"


class SharePointRootFolder(StrEnum):
    PAGES = "SitePages"
    DOCUMENTS = "Shared Documents"


class SharePointFileExtension(StrEnum):
    PAGE = ".aspx"
    PDF = ".pdf"
    MP4 = ".mp4"
