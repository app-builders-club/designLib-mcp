"""End-to-end tests: real FastMCP protocol + real Supabase.

These tests exercise the full wire: designlib_mcp.server.build_server() is
constructed, wrapped in fastmcp.Client via in-memory transport, and every tool
is invoked the same way Claude Desktop would. Each `result.data` is the
structured JSON payload the client receives.

Marked `integration` — requires SUPABASE_URL + SUPABASE_ANON_KEY in env. Run with:
    pytest tests/e2e -m integration
"""

from __future__ import annotations
import time
from typing import Any

import pytest
from fastmcp import Client

from designlib_mcp.server import build_server

pytestmark = pytest.mark.integration


EXPECTED_TOOLS = {
    "list_styles", "get_style", "list_style_facets",
    "list_palettes", "get_palette", "list_palette_facets",
    "list_font_pairs", "get_font_pair", "list_font_pair_facets",
    "list_domains", "get_domain", "list_domain_facets",
}


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


async def test_server_exposes_12_tools(client):
    tools = await client.list_tools()
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS, f"mismatch: missing={EXPECTED_TOOLS - names}, extra={names - EXPECTED_TOOLS}"


async def test_all_tools_marked_readonly(client):
    tools = await client.list_tools()
    for t in tools:
        ann = t.annotations
        assert ann is not None, f"{t.name} missing annotations"
        assert ann.readOnlyHint is True, f"{t.name} not marked readOnlyHint"
        assert ann.destructiveHint is False, f"{t.name} has destructiveHint=True"


async def test_style_facets_web_returns_expected_shape(client):
    data = await _data(client, "list_style_facets", {"platform": "web"})
    assert data["meta"]["entity_type"] == "style_facets"
    for key in ("families", "tones", "densities", "appearances", "tag_vocabulary"):
        assert key in data, f"missing facet key: {key}"
    assert len(data["families"]) > 0


async def test_style_facets_ios_has_10_families(client):
    data = await _data(client, "list_style_facets", {"platform": "ios"})
    assert len(data["families"]) == 10, f"expected 10 iOS families, got {len(data['families'])}"


async def test_list_styles_web_paginates(client):
    data = await _data(client, "list_styles", {"platform": "web", "limit": 5, "offset": 0})
    assert data["meta"]["entity_type"] == "style_list"
    assert data["total_count"] >= len(data["items"])
    assert len(data["items"]) <= 5
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert "id" in first and "name" in first


async def test_get_style_roundtrip_with_cross_links(client):
    listing = await _data(client, "list_styles", {"platform": "web", "limit": 1})
    style_id = listing["items"][0]["id"]

    start = time.perf_counter()
    style = await _data(client, "get_style", {"style_id": style_id, "include_cross_links": True})
    elapsed = time.perf_counter() - start

    assert style["id"] == style_id
    assert style["meta"]["entity_type"] == "style"
    assert "cross_links" in style
    assert "palettes" in style["cross_links"]
    assert "font_pairs" in style["cross_links"]
    assert "domains" in style["cross_links"]
    assert elapsed < 2.0, f"get_style took {elapsed:.2f}s (spec target: <1s; allowing 2s headroom)"


async def test_get_style_unknown_returns_error_payload(client):
    data = await _data(client, "get_style", {"style_id": "definitely_does_not_exist_xyz"})
    assert data["error_code"] == "NOT_FOUND"
    assert data["suggest_tool"] == "list_styles"


async def test_palette_roundtrip(client):
    facets = await _data(client, "list_palette_facets", {"platform": "web"})
    assert facets["meta"]["entity_type"] == "palette_facets"

    listing = await _data(client, "list_palettes", {"platform": "web", "limit": 3})
    assert listing["meta"]["entity_type"] == "palette_list"
    assert len(listing["items"]) > 0
    palette_id = listing["items"][0]["id"]

    palette = await _data(client, "get_palette", {"palette_id": palette_id})
    assert palette["id"] == palette_id
    assert palette["meta"]["entity_type"] == "palette"


async def test_font_pair_roundtrip(client):
    facets = await _data(client, "list_font_pair_facets", {"platform": "web"})
    assert facets["meta"]["entity_type"] == "font_pair_facets"

    listing = await _data(client, "list_font_pairs", {"platform": "web", "limit": 3})
    assert listing["meta"]["entity_type"] == "font_pair_list"
    assert len(listing["items"]) > 0
    fp_id = listing["items"][0]["id"]

    fp = await _data(client, "get_font_pair", {"font_pair_id": fp_id})
    assert fp["id"] == fp_id
    assert fp["meta"]["entity_type"] == "font_pair"


async def test_domain_roundtrip_with_recommendations(client):
    facets = await _data(client, "list_domain_facets")
    assert facets["meta"]["entity_type"] == "domain_facets"

    listing = await _data(client, "list_domains", {"limit": 3})
    assert listing["meta"]["entity_type"] == "domain_list"
    assert len(listing["items"]) > 0
    domain_id = listing["items"][0]["id"]

    domain = await _data(client, "get_domain", {"domain_id": domain_id, "platform": "web", "top_n": 3})
    assert domain["id"] == domain_id
    assert domain["meta"]["entity_type"] == "domain"
    assert "recommendations" in domain
    for key in ("styles", "palettes", "font_pairs"):
        assert key in domain["recommendations"], f"recommendations missing {key}"


async def test_ios_platform_returns_nonempty(client):
    styles = await _data(client, "list_styles", {"platform": "ios", "limit": 10})
    assert len(styles["items"]) > 0, "no iOS styles ingested"
    palettes = await _data(client, "list_palettes", {"platform": "ios", "limit": 10})
    assert len(palettes["items"]) > 0, "no iOS palettes ingested"
    fonts = await _data(client, "list_font_pairs", {"platform": "ios", "limit": 10})
    assert len(fonts["items"]) > 0, "no iOS font pairs ingested"
