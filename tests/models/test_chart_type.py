import pytest
from pydantic import ValidationError

from designlib_mcp.models.chart_type import (
    ChartType, ChartTypeSummary, ChartTypeFacets,
)
from designlib_mcp.models.common import ResponseMeta


def test_summary_minimal():
    s = ChartTypeSummary(
        id="chart_line_trend_over_time",
        data_type="Trend Over Time",
        best_chart_type="Line Chart",
        a11y_grade="AA",
    )
    assert s.library_recommendation == []


def test_full_forbids_extra_fields():
    with pytest.raises(ValidationError):
        ChartType(
            id="x", data_type="X", best_chart_type="Bar",
            when_to_use="t", when_not_to_use="t", a11y_grade="AA",
            meta=ResponseMeta(entity_type="chart_type"),
            bogus="nope",
        )


def test_full_rejects_invalid_a11y_grade():
    with pytest.raises(ValidationError):
        ChartType(
            id="x", data_type="X", best_chart_type="Bar",
            when_to_use="t", when_not_to_use="t", a11y_grade="E",
            meta=ResponseMeta(entity_type="chart_type"),
        )


def test_facets_shape():
    f = ChartTypeFacets(
        data_types=[{"value": "Trend Over Time", "count": 4}],
        a11y_grades=[{"value": "AA", "count": 10}],
        libraries=[{"value": "Chart.js", "count": 8}],
        interactive_levels=[{"value": "Hover + Zoom", "count": 3}],
        meta=ResponseMeta(entity_type="chart_type_facets"),
    )
    assert len(f.data_types) == 1
