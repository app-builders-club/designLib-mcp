"""Integration tests for inspiration_pages repository methods.

Skipped automatically if Supabase env vars are not set, AND will only fully
exercise once migration 006 is applied + ingest has loaded rows.
"""
import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository


pytestmark = pytest.mark.integration


def test_list_inspiration_pages_returns_rows(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_inspiration_pages(limit=5)
    assert "items" in out
    assert out["limit"] == 5
    assert out["offset"] == 0


def test_list_filter_by_page_type(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_inspiration_pages(page_type="marketing_landing", limit=10)
    for item in out["items"]:
        assert item["page_type"] == "marketing_landing"


def test_get_inspiration_page_missing(settings):
    repo = PostgresRepository.from_settings(settings)
    assert repo.get_inspiration_page("page_definitely_not_real") is None


def test_inspiration_page_facets(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_inspiration_page_facets()
    for key in (
        "page_types", "appearances", "densities", "style_families",
        "industries", "moods", "visual_signatures",
        "good_for_product_types", "good_for_stages",
    ):
        assert key in facets
