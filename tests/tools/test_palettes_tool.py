import pytest
from designlib_mcp.repository.supabase_repo import SupabaseRepository
from designlib_mcp.tools.palettes import (
    list_palettes_handler, get_palette_handler, list_palette_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_palettes_handler(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_palettes_handler(repo, platform="ios", limit=5)
    assert out["meta"]["entity_type"] == "palette_list"
    assert len(out["items"]) >= 1


def test_get_palette_unknown_returns_error(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = get_palette_handler(repo, palette_id="not_a_real_palette_xyz")
    assert out["error_code"] == "NOT_FOUND"


def test_list_palette_facets_handler(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_palette_facets_handler(repo, platform="ios")
    assert out["meta"]["entity_type"] == "palette_facets"
