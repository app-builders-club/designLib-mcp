from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field

from designlib_mcp.models.common import ResponseMeta


class IconSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    icon_name: str
    category: str
    library_name: str
    style: str | None = None


class Icon(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    category: str
    icon_name: str
    keywords: list[str] = Field(default_factory=list)
    library_id: str | None = None
    library_name: str
    import_code: str
    usage: str
    best_for: str | None = None
    style: str | None = None
    meta: ResponseMeta


class IconFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categories: list
    libraries: list
    styles: list
    meta: ResponseMeta
