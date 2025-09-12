from dataclasses import dataclass


@dataclass
class FluidTopicsDocument:
    id: str | None
    file_name: str | None
    title: str | None
    mime_type: str | None
    created_date: str | None
    modified_date: str | None
    url: str | None
    viewer_url: str | None
