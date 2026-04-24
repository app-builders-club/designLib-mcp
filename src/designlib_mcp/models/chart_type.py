from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from designlib_mcp.models.common import ResponseMeta


A11yGrade = Literal["AAA", "AA", "A", "B", "C", "D"]


class ChartTypeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    data_type: str
    best_chart_type: str
    a11y_grade: A11yGrade
    library_recommendation: list[str] = Field(default_factory=list)


class ChartType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    data_type: str
    keywords: list[str] = Field(default_factory=list)
    best_chart_type: str
    secondary_options: list[str] = Field(default_factory=list)
    when_to_use: str
    when_not_to_use: str
    data_volume_threshold: str | None = None
    color_guidance: str | None = None
    a11y_grade: A11yGrade
    a11y_notes: str | None = None
    a11y_fallback: str | None = None
    library_recommendation: list[str] = Field(default_factory=list)
    interactive_level: str | None = None
    meta: ResponseMeta


class ChartTypeFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_types: list
    a11y_grades: list
    libraries: list
    interactive_levels: list
    meta: ResponseMeta
