"""Pure-unit tests for the inspiration_pages normalizer.

Covers the use_when truncation in summaries (TODO 3 in
designlib-mcp-todo.md) and the full → dict round-trip.
"""
from designlib_mcp.repository.normalizer import (
    _to_inspiration_page_summary,
    _to_inspiration_page_full,
)


def test_summary_passes_use_when_through_under_limit():
    short = "Use when designing for fintech."
    out = _to_inspiration_page_summary({
        "id": "page_x", "page_type": "about", "appearance": "light",
        "screenshot_path": "images/x.jpg", "description": "d",
        "use_when": short,
    })
    assert out["use_when"] == short


def test_summary_truncates_use_when_at_120_chars():
    long = "x" * 200
    out = _to_inspiration_page_summary({
        "id": "page_x", "page_type": "about", "appearance": "light",
        "screenshot_path": "images/x.jpg", "description": "d",
        "use_when": long,
    })
    assert out["use_when"] is not None
    assert len(out["use_when"]) == 120


def test_summary_handles_missing_use_when():
    out = _to_inspiration_page_summary({
        "id": "page_x", "page_type": "about", "appearance": "light",
        "screenshot_path": "images/x.jpg", "description": "d",
    })
    assert out["use_when"] is None


def test_full_round_trips_use_when_and_generation_prompt():
    out = _to_inspiration_page_full({
        "id": "page_x", "page_type": "about", "appearance": "light",
        "screenshot_path": "images/x.jpg", "captured_at": "2026-04-24",
        "description": "d", "why_it_works": "w",
        "use_when": "Use when X.",
        "generation_prompt": "A long-scroll about page that...",
    })
    assert out["use_when"] == "Use when X."
    assert out["generation_prompt"].startswith("A long-scroll")
