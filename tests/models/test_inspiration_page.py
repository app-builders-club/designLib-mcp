import pytest
from pydantic import ValidationError

from designlib_mcp.models.inspiration_page import (
    InspirationPage, InspirationPageSummary, InspirationPageFacets,
)
from designlib_mcp.models.common import ResponseMeta


def test_summary_minimal():
    s = InspirationPageSummary(
        id="page_eddie_landing",
        page_type="marketing_landing",
        appearance="light",
        screenshot_path="images/landing/eddie.jpg",
        description="A French EV charging landing.",
    )
    assert s.id == "page_eddie_landing"
    assert s.style_family is None
    assert s.mood == []


def test_summary_with_optional_fields():
    s = InspirationPageSummary(
        id="page_x",
        page_type="about",
        appearance="dark",
        style_family="editorial",
        industry="media",
        mood=["editorial", "calm"],
        keywords=["k1", "k2"],
        screenshot_path="images/about/x.jpg",
        description="Desc.",
        use_when="Use when designing for editorial publications.",
    )
    assert s.style_family == "editorial"
    assert s.mood == ["editorial", "calm"]
    assert s.use_when.startswith("Use when")


def test_full_use_when_round_trips():
    p = InspirationPage(
        id="page_x",
        source="land-book",
        captured_at="2026-04-24",
        screenshot_path="images/x.jpg",
        page_type="about",
        appearance="light",
        description="d",
        why_it_works="w",
        use_when="Use when the team's identity is the product.",
        meta=ResponseMeta(entity_type="inspiration_page"),
    )
    assert p.use_when.startswith("Use when")
    assert p.generation_prompt is None


def test_full_minimum_fields():
    p = InspirationPage(
        id="page_x",
        source="land-book",
        captured_at="2026-04-24",
        screenshot_path="images/landing/x.jpg",
        page_type="marketing_landing",
        appearance="light",
        description="d",
        why_it_works="w",
        meta=ResponseMeta(entity_type="inspiration_page"),
    )
    assert p.url_guess is None
    assert p.density is None
    assert p.mood == []
    assert p.palette == {}


def test_full_forbids_extra():
    with pytest.raises(ValidationError):
        InspirationPage(
            id="page_x", source="land-book", captured_at="2026-04-24",
            screenshot_path="images/x.jpg",
            page_type="marketing_landing", appearance="light",
            description="d", why_it_works="w", bogus="nope",
            meta=ResponseMeta(entity_type="inspiration_page"),
        )


def test_facets_shape():
    f = InspirationPageFacets(
        page_types=[{"value": "marketing_landing", "count": 73}],
        appearances=[{"value": "light", "count": 266}],
        densities=[{"value": "comfortable", "count": 100}],
        style_families=[{"value": "editorial", "count": 5}],
        industries=[{"value": "fintech", "count": 10}],
        moods=[{"value": "playful", "count": 50}],
        visual_signatures=[{"value": "rounded_card_corners", "count": 30}],
        good_for_product_types=[{"value": "consumer_app", "count": 20}],
        good_for_stages=[{"value": "hero_section", "count": 80}],
        meta=ResponseMeta(entity_type="inspiration_page_facets"),
    )
    assert len(f.page_types) == 1
