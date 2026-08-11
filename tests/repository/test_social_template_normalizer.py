from designlib_mcp.repository.normalizer import (
    _to_social_template_full, _to_social_template_summary,
)

ROW = {
    "id": "social_story_test",
    "title": "Test Story",
    "description": "Two-slide story template.",
    "why_it_works": "One idea per slide.",
    "content_brief": "Open with a hook.",
    "format": "story",
    "aspect_ratio": "9:16",
    "appearance": "dark",
    "category": "educational",
    "slide_count": 2,
    "min_slides": 1,
    "max_slides": 4,
    "platform_fit": ["instagram"],
    "style_tags": ["minimal"],
    "use_when": ["tips_series"],
    "keywords": ["story", "tips"],
    "industry_fit": ["creator"],
    "slides": [{"index": 1, "role": "hook", "layout_note": "x", "slots": []}],
    "fonts": [{"role": "display", "family": "Inter", "fallback": "sans-serif"}],
    "html_template": "<style>:root{}</style><section class=\"slide\"></section>",
    "source": "original",
    "source_url": None,
    "source_note": None,
    "preview_path": "local/render.png",
    "sort_order": 0,
    "created_at": "2026-07-25",
}


def test_summary_excludes_html_but_reports_size():
    s = _to_social_template_summary(ROW)
    assert "html_template" not in s
    assert s["html_chars"] == len(ROW["html_template"])
    assert s["format"] == "story"
    assert s["min_slides"] == 1 and s["max_slides"] == 4


def test_full_includes_html_by_default():
    f = _to_social_template_full(ROW)
    assert f["html_template"] == ROW["html_template"]
    assert f["html_omitted"] is False
    assert f["slides"] == ROW["slides"]
    assert f["fonts"] == ROW["fonts"]
    assert f["content_brief"] == "Open with a hook."
    assert "preview_path" not in f
    assert "created_at" not in f
    assert "sort_order" not in f


def test_full_include_html_false_omits_payload():
    f = _to_social_template_full(ROW, include_html=False)
    assert "html_template" not in f
    assert f["html_omitted"] is True
    assert f["html_chars"] == len(ROW["html_template"])


def test_full_defensive_on_missing_fields():
    f = _to_social_template_full({"id": "social_x"})
    assert f["title"] == "social_x"
    assert f["slides"] == []
    assert f["source"] == "original"
    assert f["html_chars"] == 0
