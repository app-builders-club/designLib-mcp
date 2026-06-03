import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.models.common import Platform


pytestmark = pytest.mark.integration


def test_list_styles_web_returns_57_total(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_styles(Platform.WEB, limit=200)
    assert out["total_count"] == 57
    assert len(out["items"]) == 57


def test_list_styles_ios_returns_10(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_styles(Platform.IOS, limit=50)
    assert out["total_count"] == 10
    assert {s["id"] for s in out["items"]} == {
        "enterprise_muted_ios", "fitness_vitality_ios", "editorial_photography_ios",
        "minimalist_monochrome_ios", "data_dense_terminal_ios", "warm_handcrafted_ios",
        "editorial_canvas_ios", "tactile_depth_playful_ios", "youth_social_widget_ios",
        "system_default_plus_ios",
    }


def test_list_styles_filters_by_family(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_styles(Platform.WEB, family="classical")
    for s in out["items"]:
        assert s["family_id"] == "classical"


def test_list_styles_filters_by_tag(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_styles(Platform.WEB, tags=["scholarly"])
    assert len(out["items"]) >= 1
    assert any(s["id"] == "academia_classical" for s in out["items"])


def test_get_style_returns_full_tokens(settings):
    repo = PostgresRepository.from_settings(settings)
    s = repo.get_style("academia_classical")
    assert s is not None
    assert s["id"] == "academia_classical"
    assert "tokens" in s
    assert "colors" in s["tokens"]


def test_get_style_unknown_returns_none(settings):
    repo = PostgresRepository.from_settings(settings)
    assert repo.get_style("does_not_exist_xyz") is None


def test_list_style_facets_web_has_families(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_style_facets(Platform.WEB)
    assert len(facets["families"]) >= 9
    assert any(f["value"] == "polished" for f in facets["families"])
