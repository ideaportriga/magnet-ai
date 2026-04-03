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
    display_name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    parent_system_name: Optional[str] = None
