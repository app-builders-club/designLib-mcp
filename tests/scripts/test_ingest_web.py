from scripts.ingest_web import WEB_TABLES, SKIP_TABLES


def test_skip_tables_excludes_user_data_and_views():
    assert "profiles" in SKIP_TABLES
    assert "projects" in SKIP_TABLES
    assert "domain_density_mapping" in SKIP_TABLES
    assert "domain_tone_mapping" in SKIP_TABLES
    assert "style_family_counts" in SKIP_TABLES
    assert "_summary" in SKIP_TABLES


def test_web_tables_include_core_catalog():
    for t in ("style_families", "design_styles", "color_palettes",
              "font_pairs", "domains", "domain_categories",
              "recommendation_scores", "color_psychology",
              "font_pair_categories"):
        assert t in WEB_TABLES, f"{t} missing from WEB_TABLES"
