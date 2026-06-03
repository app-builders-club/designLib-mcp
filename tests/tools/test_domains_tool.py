import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.tools.domains import (
    list_domains_handler, get_domain_handler, list_domain_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_domains_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_domains_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "domain_list"
    assert out["total_count"] == 134


def test_get_domain_handler_web(settings):
    repo = PostgresRepository.from_settings(settings)
    list_out = list_domains_handler(repo, limit=1)
    out = get_domain_handler(repo, domain_id=list_out["items"][0]["id"], platform="web", top_n=3)
    assert out["meta"]["entity_type"] == "domain"
    assert "recommendations" in out


def test_get_domain_handler_unknown(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_domain_handler(repo, domain_id="does_not_exist_xyz", platform="web", top_n=3)
    assert out["error_code"] == "NOT_FOUND"


def test_list_domain_facets_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_domain_facets_handler(repo)
    assert out["meta"]["entity_type"] == "domain_facets"
    assert len(out["categories"]) >= 15
