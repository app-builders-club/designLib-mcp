"""End-to-end content-catalog tests: real FastMCP protocol + real Supabase.

Covers the 9 tools introduced by migration 005: chart_types, landing_patterns, icons.
Marked `integration` — requires SUPABASE_URL + SUPABASE_ANON_KEY in env.
"""
from __future__ import annotations
from typing import Any

import pytest
from fastmcp import Client

from designlib_mcp.server import build_server


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def mcp_server(settings):
    return build_server()


@pytest.fixture
async def client(mcp_server):
    async with Client(mcp_server) as c:
        yield c


async def _data(client: Client, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await client.call_tool(name, args or {})
    assert result.data is not None, f"{name} returned no structured data"
    return result.data


async def test_chart_type_roundtrip(client):
    facets = await _data(client, "list_chart_type_facets")
    assert facets["meta"]["entity_type"] == "chart_type_facets"
    assert len(facets["a11y_grades"]) >= 1

    listing = await _data(client, "list_chart_types", {"limit": 5})
    assert listing["meta"]["entity_type"] == "chart_type_list"
    assert listing["total_count"] == 25
    assert len(listing["items"]) > 0
    chart_id = listing["items"][0]["id"]

    chart = await _data(client, "get_chart_type", {"chart_id": chart_id})
    assert chart["id"] == chart_id
    assert chart["meta"]["entity_type"] == "chart_type"
    assert "when_to_use" in chart

    missing = await _data(client, "get_chart_type", {"chart_id": "chart_nope_xyz"})
    assert missing["error_code"] == "NOT_FOUND"


async def test_chart_type_keyword_filter(client):
    out = await _data(client, "list_chart_types", {"keyword": "trend", "limit": 10})
    assert out["total_count"] >= 1


async def test_landing_pattern_roundtrip(client):
    facets = await _data(client, "list_landing_pattern_facets")
    assert facets["meta"]["entity_type"] == "landing_pattern_facets"

    listing = await _data(client, "list_landing_patterns", {"limit": 5})
    assert listing["meta"]["entity_type"] == "landing_pattern_list"
    assert listing["total_count"] == 34
    pattern_id = listing["items"][0]["id"]

    pattern = await _data(client, "get_landing_pattern", {"pattern_id": pattern_id})
    assert pattern["id"] == pattern_id
    assert pattern["meta"]["entity_type"] == "landing_pattern"
    assert "section_order" in pattern

    missing = await _data(client, "get_landing_pattern", {"pattern_id": "landing_nope"})
    assert missing["error_code"] == "NOT_FOUND"


async def test_icon_roundtrip(client):
    facets = await _data(client, "list_icon_facets")
    assert facets["meta"]["entity_type"] == "icon_facets"
    assert any(c["value"] == "Navigation" for c in facets["categories"])

    listing = await _data(client, "list_icons", {"limit": 5})
    assert listing["meta"]["entity_type"] == "icon_list"
    assert listing["total_count"] == 105

    navigation = await _data(client, "list_icons", {"category": "Navigation", "limit": 50})
    for item in navigation["items"]:
        assert item["category"] == "Navigation"

    icon = await _data(client, "get_icon", {"icon_id": "icon_phosphor_list"})
    assert icon["id"] == "icon_phosphor_list"
    assert icon["meta"]["entity_type"] == "icon"
    assert icon["library_id"] == "phosphor"

    missing = await _data(client, "get_icon", {"icon_id": "icon_nope"})
    assert missing["error_code"] == "NOT_FOUND"
