import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.models.common import Platform


pytestmark = pytest.mark.integration


def test_list_domains_returns_134(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_domains(limit=200)
    assert out["total_count"] == 134


def test_list_domains_filter_category(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_domains(category_id="travel")
    for d in out["items"]:
        assert d["category_id"] == "travel"


def test_get_domain_web_recommendations(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_domains(limit=1)
    domain_id = out["items"][0]["id"]
    d = repo.get_domain(domain_id, Platform.WEB, top_n=3)
    assert d is not None
    assert "recommendations" in d
    assert isinstance(d["recommendations"]["styles"], list)


def test_get_domain_ios_empty_recommendations_v1(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_domains(limit=1)
    domain_id = out["items"][0]["id"]
    d = repo.get_domain(domain_id, Platform.IOS, top_n=3)
    assert d["recommendations"]["styles"] == []


def test_list_domain_facets_returns_categories(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_domain_facets()
    assert len(facets["categories"]) >= 15
