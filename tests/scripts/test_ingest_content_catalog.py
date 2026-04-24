from pathlib import Path

from scripts.ingest_content_catalog import (
    slugify, parse_keywords, parse_list,
    load_charts, load_landing, load_icons,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO_ROOT / "mcp-migration"


def test_slugify_joins_and_lowercases():
    assert slugify("Bar Chart", "Compare Categories") == "bar_chart_compare_categories"


def test_slugify_collapses_punctuation():
    assert slugify("Phosphor (primary) + Heroicons") == "phosphor_primary_heroicons"


def test_slugify_strips_edges():
    assert slugify("  --__foo--  ") == "foo"


def test_parse_keywords_comma_separated():
    out = parse_keywords("trend, time-series, line, growth")
    assert out == ["trend", "time-series", "line", "growth"]


def test_parse_keywords_space_separated():
    out = parse_keywords("hamburger menu navigation toggle bars")
    assert out == ["hamburger", "menu", "navigation", "toggle", "bars"]


def test_parse_keywords_dedupe_and_lowercase():
    out = parse_keywords("A, a, B b, b")
    assert out == ["a", "b"]


def test_parse_list_preserves_multiword():
    out = parse_list("Area Chart, Smooth Area, Column Chart")
    assert out == ["Area Chart", "Smooth Area", "Column Chart"]


def test_parse_list_drops_empty():
    assert parse_list("") == []
    assert parse_list(",  ,") == []


def test_load_charts_real_csv_shape():
    rows = load_charts(SOURCE / "charts.csv")
    assert len(rows) == 25
    for r in rows:
        assert r["id"].startswith("chart_")
        assert r["a11y_grade"] in {"AAA", "AA", "A", "B", "C", "D"}
        assert isinstance(r["keywords"], list)
        assert isinstance(r["library_recommendation"], list)
        assert r["sort_order"] >= 1


def test_load_landing_real_csv_shape():
    rows = load_landing(SOURCE / "landing.csv")
    assert len(rows) == 34
    ids = {r["id"] for r in rows}
    assert len(ids) == 34, "slug collisions leaked"
    for r in rows:
        assert r["id"].startswith("landing_")
        assert r["name"]
        assert r["primary_cta_placement"]


def test_load_icons_real_csv_shape_no_client():
    rows = load_icons(SOURCE / "icons.csv", client=None)
    assert len(rows) == 105
    ids = {r["id"] for r in rows}
    assert len(ids) == 105, "slug collisions leaked"
    for r in rows:
        assert r["id"].startswith("icon_")
        assert r["library_id"] is None  # no client, no lookup
        assert r["library_name"]
        assert r["import_code"]
