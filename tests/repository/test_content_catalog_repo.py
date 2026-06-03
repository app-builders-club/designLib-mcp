import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository


pytestmark = pytest.mark.integration


# ---- chart_types ----

def test_list_chart_types_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_chart_types(limit=100)
    assert out["total_count"] == 25


def test_list_chart_types_filter_by_a11y_grade(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_chart_types(a11y_grade="AAA", limit=100)
    assert out["total_count"] >= 1
    for item in out["items"]:
        assert item["a11y_grade"] == "AAA"


def test_list_chart_types_filter_by_keyword(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_chart_types(keyword="trend", limit=100)
    assert out["total_count"] >= 1


def test_get_chart_type_returns_full(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = repo.list_chart_types(limit=1)
    cid = listing["items"][0]["id"]
    full = repo.get_chart_type(cid)
    assert full is not None
    assert "when_to_use" in full
    assert "library_recommendation" in full


def test_get_chart_type_missing(settings):
    repo = PostgresRepository.from_settings(settings)
    assert repo.get_chart_type("chart_definitely_not_real") is None


def test_chart_type_facets(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_chart_type_facets()
    assert len(facets["data_types"]) >= 1
    assert len(facets["a11y_grades"]) >= 1


# ---- landing_patterns ----

def test_list_landing_patterns_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_landing_patterns(limit=100)
    assert out["total_count"] == 34


def test_list_landing_patterns_filter_by_keyword(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_landing_patterns(keyword="hero", limit=100)
    assert out["total_count"] >= 1


def test_get_landing_pattern_returns_full(settings):
    repo = PostgresRepository.from_settings(settings)
    listing = repo.list_landing_patterns(limit=1)
    pid = listing["items"][0]["id"]
    full = repo.get_landing_pattern(pid)
    assert full is not None
    assert full["id"] == pid
    assert "section_order" in full


def test_landing_pattern_facets(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_landing_pattern_facets()
    assert len(facets["cta_placements"]) >= 1


# ---- icons ----

def test_list_icons_count(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_icons(limit=200)
    assert out["total_count"] == 105


def test_list_icons_filter_by_category(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_icons(category="Navigation", limit=100)
    assert out["total_count"] >= 1
    for item in out["items"]:
        assert item["category"] == "Navigation"


def test_list_icons_filter_by_library_and_style(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_icons(library="Phosphor", style="Outline", limit=200)
    assert out["total_count"] >= 50  # most phosphor icons are outline


def test_list_icons_keyword_match(settings):
    repo = PostgresRepository.from_settings(settings)
    out = repo.list_icons(keyword="menu", limit=50)
    assert out["total_count"] >= 1


def test_get_icon_has_library_id(settings):
    repo = PostgresRepository.from_settings(settings)
    full = repo.get_icon("icon_phosphor_list")
    assert full is not None
    assert full["library_id"] == "phosphor"
    assert full["import_code"].startswith("import")


def test_icon_facets(settings):
    repo = PostgresRepository.from_settings(settings)
    facets = repo.list_icon_facets()
    assert len(facets["categories"]) >= 3
    assert any(c["value"] == "Navigation" for c in facets["categories"])
