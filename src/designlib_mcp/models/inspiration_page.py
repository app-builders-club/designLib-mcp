from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from designlib_mcp.models.common import ResponseMeta


class InspirationPageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    page_type: str
    appearance: str
    style_family: str | None = None
    industry: str | None = None
    mood: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    screenshot_path: str
    description: str
    use_when: str | None = None


class InspirationPage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source: str
    url_guess: str | None = None
    captured_at: str
    screenshot_path: str

    page_type: str
    landing_pattern_id: str | None = None
    style_family: str | None = None
    industry: str | None = None
    product_category: str | None = None
    audience: str | None = None
    appearance: str
    density: str | None = None
    mood: list[str] = Field(default_factory=list)

    visual_signatures: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    good_for_product_types: list[str] = Field(default_factory=list)
    good_for_moods: list[str] = Field(default_factory=list)
    good_for_stages: list[str] = Field(default_factory=list)
    section_order: list[str] = Field(default_factory=list)

    palette: dict[str, Any] = Field(default_factory=dict)
    typography: dict[str, Any] = Field(default_factory=dict)
    primary_cta: dict[str, Any] | None = None
    sections: list[dict[str, Any]] = Field(default_factory=list)
    inspiration_metadata: dict[str, Any] = Field(default_factory=dict)
    reference_for: dict[str, Any] = Field(default_factory=dict)
    effects: list[Any] = Field(default_factory=list)
    interaction_cues: list[Any] = Field(default_factory=list)
    generation_constraints: dict[str, Any] | None = None

    description: str
    why_it_works: str
    generation_prompt: str | None = None
    use_when: str | None = None
    notes: str | None = None
    meta: ResponseMeta


class InspirationPageFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page_types: list
    appearances: list
    densities: list
    style_families: list
    industries: list
    moods: list
    visual_signatures: list
    good_for_product_types: list
    good_for_stages: list
    meta: ResponseMeta
