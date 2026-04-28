"""Unit tests for the inspiration_pages tool layer using a fake repo (no Supabase)."""
from __future__ import annotations
from typing import Any

from designlib_mcp.tools.inspiration_pages import (
    list_inspiration_pages_handler,
    get_inspiration_page_handler,
    list_inspiration_page_facets_handler,
)


class _FakeRepo:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] = {}

    def list_inspiration_pages(self, **kwargs: Any) -> dict[str, Any]:
        self.last_kwargs = kwargs
        return {
            "items": [{
                "id": "page_x",
                "page_type": "marketing_landing",
                "appearance": "light",
                "style_family": "editorial",
                "industry": "fintech",
                "mood": ["calm"],
                "keywords": ["a", "b"],
                "screenshot_path": "images/x.jpg",
                "description": "desc",
                "use_when": "Use when designing for fintech.",
            }],
            "total_count": 1,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
        }

    def get_inspiration_page(self, page_id: str) -> dict[str, Any] | None:
        if page_id == "page_x":
            return {
                "id": "page_x",
                "source": "land-book",
                "captured_at": "2026-04-24",
                "screenshot_path": "images/x.jpg",
                "page_type": "marketing_landing",
                "appearance": "light",
                "description": "d",
                "why_it_works": "w",
            }
        return None

    def list_inspiration_page_facets(self) -> dict[str, Any]:
        return {
            "page_types": [{"value": "marketing_landing", "count": 1}],
            "appearances": [], "densities": [],
            "style_families": [], "industries": [],
            "moods": [], "visual_signatures": [],
            "good_for_product_types": [], "good_for_stages": [],
        }


def test_list_handler_default_limit_and_meta():
    repo = _FakeRepo()
    out = list_inspiration_pages_handler(repo)
    assert out["meta"]["entity_type"] == "inspiration_page_list"
    assert out["meta"]["platform"] is None
    assert out["limit"] == 25
    assert out["offset"] == 0
    assert out["items"][0]["id"] == "page_x"
    assert out["items"][0]["use_when"].startswith("Use when")


def test_list_handler_passes_filters():
    repo = _FakeRepo()
    list_inspiration_pages_handler(
        repo, page_type="marketing_landing", mood="playful",
        signature="pill_cta_buttons", good_for_product_type="consumer_app",
        keyword="hero", limit=5, offset=10,
    )
    assert repo.last_kwargs["page_type"] == "marketing_landing"
    assert repo.last_kwargs["mood"] == "playful"
    assert repo.last_kwargs["signature"] == "pill_cta_buttons"
    assert repo.last_kwargs["good_for_product_type"] == "consumer_app"
    assert repo.last_kwargs["keyword"] == "hero"
    assert repo.last_kwargs["limit"] == 5
    assert repo.last_kwargs["offset"] == 10


def test_get_handler_found():
    repo = _FakeRepo()
    out = get_inspiration_page_handler(repo, page_id="page_x")
    assert out["id"] == "page_x"
    assert out["meta"]["entity_type"] == "inspiration_page"


def test_get_handler_not_found_returns_error():
    repo = _FakeRepo()
    out = get_inspiration_page_handler(repo, page_id="page_missing")
    assert out["error_code"] == "NOT_FOUND"
    assert out["field"] == "page_id"
    assert out["suggest_tool"] == "list_inspiration_pages"


def test_facets_handler_meta():
    repo = _FakeRepo()
    out = list_inspiration_page_facets_handler(repo)
    assert out["meta"]["entity_type"] == "inspiration_page_facets"
    assert out["page_types"][0]["value"] == "marketing_landing"
