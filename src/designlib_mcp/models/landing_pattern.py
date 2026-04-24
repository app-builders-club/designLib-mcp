from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field

from designlib_mcp.models.common import ResponseMeta


class LandingPatternSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    primary_cta_placement: str


class LandingPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    keywords: list[str] = Field(default_factory=list)
    section_order: str
    primary_cta_placement: str
    color_strategy: str | None = None
    recommended_effects: str | None = None
    conversion_optimization: str | None = None
    meta: ResponseMeta


class LandingPatternFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cta_placements: list
    meta: ResponseMeta
