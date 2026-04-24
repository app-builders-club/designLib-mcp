from designlib_mcp.repository.base import CatalogRepository


def test_protocol_has_required_methods():
    methods = {
        "list_styles", "get_style", "list_style_facets",
        "list_palettes", "get_palette", "list_palette_facets",
        "list_font_pairs", "get_font_pair", "list_font_pair_facets",
        "list_domains", "get_domain", "list_domain_facets",
        "list_chart_types", "get_chart_type", "list_chart_type_facets",
        "list_landing_patterns", "get_landing_pattern", "list_landing_pattern_facets",
        "list_icons", "get_icon", "list_icon_facets",
    }
    for m in methods:
        assert hasattr(CatalogRepository, m), f"missing {m}"
