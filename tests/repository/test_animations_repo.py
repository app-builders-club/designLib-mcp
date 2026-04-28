"""Integration tests for the animations repository methods.

Requires migration 008 applied and staging ingested via scripts/ingest_animations.py.
"""
import pytest
from designlib_mcp.repository.supabase_repo import SupabaseRepository


pytestmark = pytest.mark.integration


def test_list_animations_returns_results(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = repo.list_animations(limit=200)
    assert out["total_count"] >= 1
    assert "items" in out
    item = out["items"][0]
    assert "id" in item
    assert "title" in item
    assert "category" in item


def test_list_animations_filter_by_category(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = repo.list_animations(category="background", limit=200)
    for item in out["items"]:
        assert item["category"] == "background"


def test_list_animations_filter_by_framework(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = repo.list_animations(framework="react", limit=200)
    for item in out["items"]:
        assert item["framework"] == "react"


def test_list_animations_filter_by_keyword(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = repo.list_animations(keyword="gradient", limit=200)
    assert out["total_count"] >= 0


def test_list_animations_filter_by_use_when(settings):
    repo = SupabaseRepository.from_settings(settings)
    facets = repo.list_animation_facets()
    if not facets["use_when"]:
        pytest.skip("no use_when values yet")
    sample = facets["use_when"][0]["value"]
    out = repo.list_animations(use_when=sample, limit=200)
    assert out["total_count"] >= 1


def test_get_animation_returns_full(settings):
    repo = SupabaseRepository.from_settings(settings)
    listing = repo.list_animations(limit=1)
    aid = listing["items"][0]["id"]
    full = repo.get_animation(aid)
    assert full is not None
    assert "prompt_text" in full
    assert "component_filename" in full
    assert full["id"] == aid


def test_get_animation_missing(settings):
    repo = SupabaseRepository.from_settings(settings)
    assert repo.get_animation("animation_definitely_not_real") is None


def test_animation_facets(settings):
    repo = SupabaseRepository.from_settings(settings)
    facets = repo.list_animation_facets()
    for axis in ("categories", "frameworks", "libraries", "interactivity",
                 "complexity", "style_tags", "placement", "use_when"):
        assert axis in facets
        assert isinstance(facets[axis], list)
    assert len(facets["categories"]) >= 1
    assert len(facets["frameworks"]) >= 1
