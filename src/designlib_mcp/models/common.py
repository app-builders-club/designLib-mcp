from __future__ import annotations
from enum import Enum
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class Platform(str, Enum):
    WEB = "web"
    IOS = "ios"


class Appearance(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    BOTH = "both"


class Density(str, Enum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    SPACIOUS = "spacious"


class ResponseMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    platform: Platform | None = None
    entity_type: str
    truncated: bool = False


class FacetValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str
    count: int = Field(ge=0)
    label: str | None = None


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    items: list[T]
    total_count: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    meta: ResponseMeta


class MCPError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error_code: str
    message: str
    field: str | None = None
    available_values: list[str] | None = None
    suggest_tool: str | None = None
