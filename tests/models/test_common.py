import pytest
from pydantic import ValidationError
from designlib_mcp.models.common import (
    Platform, Appearance, Density, ResponseMeta, FacetValue,
    PaginatedResponse, MCPError,
)


def test_platform_enum_values():
    assert Platform.WEB.value == "web"
    assert Platform.IOS.value == "ios"


def test_response_meta_defaults():
    meta = ResponseMeta(entity_type="style")
    assert meta.schema_version == "1.0"
    assert meta.truncated is False
    assert meta.platform is None


def test_facet_value_serialization():
    f = FacetValue(value="polished", count=12, label="Polished")
    assert f.model_dump() == {"value": "polished", "count": 12, "label": "Polished"}


def test_paginated_response_generic():
    items = [FacetValue(value="a", count=1)]
    resp = PaginatedResponse[FacetValue](
        items=items, total_count=1, limit=50, offset=0,
        meta=ResponseMeta(entity_type="facet"),
    )
    assert resp.items[0].value == "a"
    assert resp.total_count == 1


def test_mcp_error_actionable():
    err = MCPError(
        error_code="UNKNOWN_FAMILY",
        message="Unknown family 'foo'.",
        field="family",
        available_values=["polished", "dark"],
        suggest_tool="list_style_facets",
    )
    payload = err.model_dump()
    assert payload["error_code"] == "UNKNOWN_FAMILY"
    assert payload["available_values"] == ["polished", "dark"]


def test_density_enum_rejects_unknown():
    with pytest.raises(ValueError):
        Density("crowded")
