import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.models.common import Platform


pytestmark = pytest.mark.integration


def test_list_palettes_web_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_palettes(Platform.WEB, limit=200)
    assert out["total_count"] == 87


def test_list_palettes_ios_includes_aggregated(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_palettes(Platform.IOS, limit=50)
    assert out["total_count"] >= 10
    for p in out["items"]:
        assert p["platform"] == "ios"


def test_get_palette_returns_full_roles(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_palettes(Platform.IOS, limit=1)
    pid = out["items"][0]["id"]
    p = repo.get_palette(pid)
    assert p is not None
    assert "roles" in p
    assert isinstance(p["roles"], list)


def test_list_palette_facets_returns_appearances(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_palette_facets(Platform.IOS)
    appearance_values = {a["value"] for a in facets["appearances"]}
    assert "light" in appearance_values
