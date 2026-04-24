import pytest
from pydantic import ValidationError

from designlib_mcp.models.landing_pattern import (
    LandingPattern, LandingPatternSummary, LandingPatternFacets,
)
from designlib_mcp.models.common import ResponseMeta


def test_summary_minimal():
    s = LandingPatternSummary(
        id="landing_hero_features_cta",
        name="Hero + Features + CTA",
        primary_cta_placement="Hero (sticky) + Bottom",
    )
    assert s.id == "landing_hero_features_cta"


def test_full_forbids_extra():
    with pytest.raises(ValidationError):
        LandingPattern(
            id="x", name="X", section_order="1. Hero",
            primary_cta_placement="Hero", bogus="nope",
            meta=ResponseMeta(entity_type="landing_pattern"),
        )


def test_full_optional_fields_none():
    p = LandingPattern(
        id="landing_minimal", name="Minimal",
        keywords=["minimal", "clean"],
        section_order="1. Hero, 2. CTA",
        primary_cta_placement="Center",
        meta=ResponseMeta(entity_type="landing_pattern"),
    )
    assert p.color_strategy is None
    assert p.recommended_effects is None
    assert p.conversion_optimization is None


def test_facets_shape():
    f = LandingPatternFacets(
        cta_placements=[{"value": "Hero (sticky) + Bottom", "count": 3}],
        meta=ResponseMeta(entity_type="landing_pattern_facets"),
    )
    assert len(f.cta_placements) == 1
