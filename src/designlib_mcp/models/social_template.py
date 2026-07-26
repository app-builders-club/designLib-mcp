from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from designlib_mcp.models.common import ResponseMeta

Format = Literal["story", "carousel"]
AspectRatio = Literal["9:16", "4:5", "1:1"]
TemplateAppearance = Literal["light", "dark", "mixed"]
TemplateCategory = Literal[
    "promo", "product_showcase", "educational", "listicle", "checklist",
    "quote", "announcement", "testimonial", "personal_story", "before_after",
    "event", "engagement",
]
SlideRole = Literal["hook", "content", "proof", "recap", "cta"]
SlotType = Literal[
    "headline", "subhead", "body", "bullet_list", "cta", "kicker", "quote",
    "stat", "badge", "handle", "image_slot", "avatar_slot", "logo_slot",
]
PlatformFit = Literal["instagram", "tiktok", "linkedin", "facebook"]
Source = Literal[
    "canva_gallery", "adobe_express_gallery", "dribbble", "behance",
    "original", "other",
]


class Slot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: SlotType
    max_chars: int | None = None
    required: bool = True
    hint: str | None = None
    example: str | None = None


class Slide(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int
    role: SlideRole
    layout_note: str
    repeatable: bool = False
    slots: list[Slot] = Field(default_factory=list)


class FontSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str
    family: str
    google_font: bool = True
    weights: list[int] = Field(default_factory=list)
    fallback: str


class SocialTemplateSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    description: str
    format: Format
    category: TemplateCategory
    aspect_ratio: AspectRatio
    appearance: TemplateAppearance
    slide_count: int
    min_slides: int
    max_slides: int
    platform_fit: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    html_chars: int


class SocialTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    description: str
    why_it_works: str
    content_brief: str
    format: Format
    category: TemplateCategory
    aspect_ratio: AspectRatio
    appearance: TemplateAppearance
    slide_count: int
    min_slides: int
    max_slides: int
    platform_fit: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    use_when: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    industry_fit: list[str] = Field(default_factory=list)
    slides: list[Slide] = Field(default_factory=list)
    fonts: list[FontSpec] = Field(default_factory=list)
    html_template: str | None = None
    html_omitted: bool = False
    html_chars: int
    source: Source
    source_url: str | None = None
    source_note: str | None = None
    meta: ResponseMeta


class SocialTemplateFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    formats: list
    categories: list
    aspect_ratios: list
    appearances: list
    platforms: list
    style_tags: list
    use_when: list
    industries: list
    meta: ResponseMeta
