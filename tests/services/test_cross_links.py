import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.services.cross_links import (
    cross_links_for_style, recommendations_for_domain,
)
from designlib_mcp.models.common import Platform


pytestmark = pytest.mark.integration


def test_cross_links_for_web_style(settings):
    repo = PostgresRepository.from_settings(settings)
    out = cross_links_for_style(repo, "academia_classical", limit=3)
    assert "palettes" in out and "font_pairs" in out and "domains" in out
    assert len(out["domains"]) <= 3


def test_cross_links_for_ios_style_empty_v1(settings):
    repo = PostgresRepository.from_settings(settings)
    out = cross_links_for_style(repo, "fitness_vitality_ios", limit=3)
    assert out["domains"] == []


def test_recommendations_for_domain_web(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_domains(limit=1)
    domain_id = out["items"][0]["id"]
    rec = recommendations_for_domain(repo, domain_id, Platform.WEB, top_n=3)
    assert "styles" in rec and "palettes" in rec and "font_pairs" in rec
