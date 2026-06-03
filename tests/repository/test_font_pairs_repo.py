import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.models.common import Platform


pytestmark = pytest.mark.integration


def test_list_font_pairs_web_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_font_pairs(Platform.WEB, limit=100)
    assert out["total_count"] == 28


def test_list_font_pairs_ios_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_font_pairs(Platform.IOS, limit=50)
    assert out["total_count"] == 6


def test_get_font_pair_full(settings):
    repo = PostgresRepository.from_settings(settings)
    fp = repo.get_font_pair("ios_sf_pro_text_display")
    assert fp is not None
    assert fp["heading"]["font_family"] == "SF Pro Display"
    assert fp["body"]["is_system_font"] is True


def test_list_font_pair_facets_returns_categories(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_font_pair_facets(Platform.IOS)
    cat_values = {c["value"] for c in facets["categories"]}
    assert "system_sans" in cat_values
