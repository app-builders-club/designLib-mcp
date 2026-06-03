import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.tools.font_pairs import (
    list_font_pairs_handler, get_font_pair_handler, list_font_pair_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_font_pairs_ios(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_font_pairs_handler(repo, platform="ios", limit=10)
    assert out["meta"]["entity_type"] == "font_pair_list"
    assert out["total_count"] == 6


def test_get_font_pair_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_font_pair_handler(repo, font_pair_id="ios_sf_pro_text_display")
    assert out["heading"]["font_family"] == "SF Pro Display"


def test_list_font_pair_facets_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_font_pair_facets_handler(repo, platform="ios")
    assert out["meta"]["entity_type"] == "font_pair_facets"
