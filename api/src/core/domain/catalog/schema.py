from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CatalogItem(BaseModel):
    id: str
    name: str
    system_name: str
    description: Optional[str] = None
    entity_type: str
    entity_label: str
    updated_at: Optional[datetime] = None
