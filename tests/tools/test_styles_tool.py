import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.models.common import Platform
from designlib_mcp.tools.styles import (
    list_styles_handler, get_style_handler, list_style_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_styles_handler_returns_paginated(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_styles_handler(repo, platform="web", limit=5, offset=0)
    assert "items" in out
    assert "total_count" in out
    assert "meta" in out
    assert out["meta"]["entity_type"] == "style_list"


def test_get_style_handler_returns_full_with_cross_links(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_style_handler(repo, style_id="academia_classical", include_cross_links=True)
    assert out["id"] == "academia_classical"
    assert out["cross_links"] is not None


def test_get_style_handler_unknown_returns_error(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_style_handler(repo, style_id="does_not_exist_xyz")
    assert out["error_code"] == "NOT_FOUND"


def test_list_style_facets_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_style_facets_handler(repo, platform="ios")
    assert out["meta"]["entity_type"] == "style_facets"
    assert len(out["families"]) == 10
