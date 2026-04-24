import pytest
from designlib_mcp.repository.supabase_repo import SupabaseRepository
from designlib_mcp.tools.chart_types import (
    list_chart_types_handler, get_chart_type_handler, list_chart_type_facets_handler,
)
from designlib_mcp.tools.landing_patterns import (
    list_landing_patterns_handler, get_landing_pattern_handler, list_landing_pattern_facets_handler,
)
from designlib_mcp.tools.icons import (
    list_icons_handler, get_icon_handler, list_icon_facets_handler,
)


pytestmark = pytest.mark.integration


def test_chart_types_handler_meta(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_chart_types_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "chart_type_list"
    assert out["meta"]["platform"] is None
    assert len(out["items"]) >= 1


def test_get_chart_type_not_found(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = get_chart_type_handler(repo, chart_id="chart_nope_xyz")
    assert out["error_code"] == "NOT_FOUND"
    assert out["suggest_tool"] == "list_chart_types"


def test_chart_type_facets_handler(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_chart_type_facets_handler(repo)
    assert out["meta"]["entity_type"] == "chart_type_facets"


def test_landing_patterns_handler_meta(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_landing_patterns_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "landing_pattern_list"


def test_get_landing_pattern_not_found(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = get_landing_pattern_handler(repo, pattern_id="landing_nope")
    assert out["error_code"] == "NOT_FOUND"
    assert out["suggest_tool"] == "list_landing_patterns"


def test_landing_pattern_facets_handler(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_landing_pattern_facets_handler(repo)
    assert out["meta"]["entity_type"] == "landing_pattern_facets"


def test_icons_handler_meta(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_icons_handler(repo, limit=5)
    assert out["meta"]["entity_type"] == "icon_list"


def test_get_icon_not_found(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = get_icon_handler(repo, icon_id="icon_nope")
    assert out["error_code"] == "NOT_FOUND"
    assert out["suggest_tool"] == "list_icons"


def test_icon_facets_handler(settings):
    repo = SupabaseRepository.from_settings(settings)
    out = list_icon_facets_handler(repo)
    assert out["meta"]["entity_type"] == "icon_facets"
