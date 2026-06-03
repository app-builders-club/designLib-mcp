import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.tools.animations import (
    list_animations_handler, get_animation_handler, list_animation_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_animations_handler_meta(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_animations_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "animation_list"
    assert out["meta"]["platform"] is None
    assert len(out["items"]) >= 1


def test_get_animation_not_found(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_animation_handler(repo, animation_id="animation_nope_xyz")
    assert out["error_code"] == "NOT_FOUND"
    assert out["suggest_tool"] == "list_animations"


def test_get_animation_full_meta(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = list_animations_handler(repo, limit=1)
    aid = listing["items"][0]["id"]
    out = get_animation_handler(repo, animation_id=aid)
    assert out["meta"]["entity_type"] == "animation"
    assert out["id"] == aid


def test_animation_facets_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_animation_facets_handler(repo)
    assert out["meta"]["entity_type"] == "animation_facets"
