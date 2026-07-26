"""Integration tests for the social_templates repository methods.

Requires migration 009 applied and seed rows loaded via
scripts/emit_social_templates_sql.py output.
"""
import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository


pytestmark = pytest.mark.integration


def test_list_social_templates_returns_results(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_social_templates(limit=200)
    assert out["total_count"] >= 1
    item = out["items"][0]
    assert "id" in item
    assert "title" in item
    assert "format" in item
    assert "html_chars" in item
    assert "html_template" not in item


def test_list_social_templates_filter_by_format(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_social_templates(format="carousel", limit=200)
    for item in out["items"]:
        assert item["format"] == "carousel"


def test_list_social_templates_filter_by_category(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_social_template_facets()
    if not facets["categories"]:
        pytest.skip("no social templates yet")
    sample = facets["categories"][0]["value"]
    out = repo.list_social_templates(category=sample, limit=200)
    assert out["total_count"] >= 1
    for item in out["items"]:
        assert item["category"] == sample


def test_list_social_templates_filter_by_platform(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_social_templates(platform="instagram", limit=200)
    for item in out["items"]:
        assert "instagram" in item["platform_fit"]


def test_list_social_templates_slides_range(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_social_templates(slides=3, limit=200)
    for item in out["items"]:
        assert item["min_slides"] <= 3 <= item["max_slides"]


def test_get_social_template_returns_full(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = repo.list_social_templates(limit=1)
    tid = listing["items"][0]["id"]
    full = repo.get_social_template(tid)
    assert full is not None
    assert full["id"] == tid
    assert full["html_template"]
    assert full["slides"]
    assert full["html_omitted"] is False


def test_get_social_template_without_html(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = repo.list_social_templates(limit=1)
    tid = listing["items"][0]["id"]
    spec = repo.get_social_template(tid, include_html=False)
    assert spec is not None
    assert "html_template" not in spec
    assert spec["html_omitted"] is True
    assert spec["html_chars"] > 0


def test_get_social_template_missing(settings):
    repo = PostgresRepository.from_settings(settings)
    assert repo.get_social_template("social_definitely_not_real") is None


def test_social_template_facets(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_social_template_facets()
    for axis in ("formats", "categories", "aspect_ratios", "appearances",
                 "platforms", "style_tags", "use_when", "industries"):
        assert axis in facets
        assert isinstance(facets[axis], list)
    assert len(facets["formats"]) >= 1
