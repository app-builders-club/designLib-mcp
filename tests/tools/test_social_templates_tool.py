import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.tools.social_templates import (
    list_social_templates_handler, get_social_template_handler,
    list_social_template_facets_handler,
)


pytestmark = pytest.mark.integration


def test_list_social_templates_handler_meta(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_social_templates_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "social_template_list"
    assert out["meta"]["platform"] is None
    assert len(out["items"]) >= 1


def test_get_social_template_not_found(settings):
    repo = PostgresRepository.from_settings(settings)
    out = get_social_template_handler(repo, template_id="social_nope_xyz")
    assert out["error_code"] == "NOT_FOUND"
    assert out["field"] == "template_id"
    assert out["suggest_tool"] == "list_social_templates"


def test_get_social_template_full_meta(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = list_social_templates_handler(repo, limit=1)
    tid = listing["items"][0]["id"]
    out = get_social_template_handler(repo, template_id=tid)
    assert out["meta"]["entity_type"] == "social_template"
    assert out["id"] == tid
    assert out["html_template"]


def test_get_social_template_spec_only(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = list_social_templates_handler(repo, limit=1)
    tid = listing["items"][0]["id"]
    out = get_social_template_handler(repo, template_id=tid, include_html=False)
    assert "html_template" not in out
    assert out["html_omitted"] is True
    assert out["html_chars"] > 0


def test_social_template_facets_handler(settings):
    repo = PostgresRepository.from_settings(settings)
    out = list_social_template_facets_handler(repo)
    assert out["meta"]["entity_type"] == "social_template_facets"
    assert "formats" in out
