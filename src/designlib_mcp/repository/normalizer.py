from __future__ import annotations
from typing import Any


def _primary_swatch(row: dict) -> str:
    tokens = row.get("tokens") or {}
    colors = tokens.get("colors") or {}
    return colors.get("primary") or colors.get("background") or "#000000"


def _to_style_summary(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row.get("name_en") or row["id"],
        "family_id": row.get("family_id") or "",
        "platform": row.get("platform", "web"),
        "short_description": (row.get("description") or "")[:200],
        "top_signatures": (row.get("visual_signatures") or [])[:3],
        "primary_swatch": _primary_swatch(row),
    }


def _to_style_full(row: dict) -> dict[str, Any]:
    family_name = ""
    sf = row.get("style_families")
    if isinstance(sf, dict):
        family_name = sf.get("name_en", "")
    elif isinstance(sf, list) and sf:
        family_name = sf[0].get("name_en", "")
    return {
        "id": row["id"],
        "name": row.get("name_en") or row["id"],
        "family_id": row.get("family_id") or "",
        "family_name": family_name,
        "platform": row.get("platform", "web"),
        "description": row.get("description") or "",
        "visual_signatures": row.get("visual_signatures") or [],
        "emotional_keywords": row.get("emotional_keywords") or [],
        "anti_patterns": row.get("anti_patterns") or [],
        "tokens": row.get("tokens") or {},
        "ios_metadata": row.get("ios_metadata"),
    }


def _to_palette_summary(row: dict) -> dict[str, Any]:
    colors = row.get("colors") or {}
    swatches = list(colors.values())[:5] if isinstance(colors, dict) else []
    appearance = "dark" if row.get("dark_mode_first") else "light"
    if isinstance(row.get("tags"), list):
        if "dark" in row["tags"] and "light" not in row["tags"]:
            appearance = "dark"
        elif "light" in row["tags"] and "dark" not in row["tags"]:
            appearance = "light"
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "platform": row.get("platform", "web"),
        "appearance": appearance,
        "main_swatches": swatches,
    }


def _to_palette_full(row: dict) -> dict[str, Any]:
    colors = row.get("colors") or {}
    roles = [{"role": role, "hex": hex_v} for role, hex_v in colors.items()] if isinstance(colors, dict) else []
    appearance = "dark" if row.get("dark_mode_first") else "light"
    tags = row.get("tags") or []
    if "dark" in tags and "light" not in tags:
        appearance = "dark"
    elif "light" in tags and "dark" not in tags:
        appearance = "light"
    source = "ios_aggregated" if "ios_aggregated" in tags else "curated"
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "platform": row.get("platform", "web"),
        "appearance": appearance,
        "roles": roles,
        "tags": tags,
        "source": source,
        "reference_apps": [],
        "used_by_styles": row.get("style_fit") or [],
    }


def _to_font_spec(jsonb: Any) -> dict[str, Any]:
    j = jsonb or {}
    return {
        "font_family": j.get("font_family") or j.get("family") or "",
        "weights": j.get("weights") or [],
        "fallbacks": j.get("fallbacks") or [],
        "google_fonts_url": j.get("google_fonts_url") or j.get("import_url"),
        "is_system_font": bool(j.get("is_system_font", False)),
    }


def _to_font_pair_summary(row: dict) -> dict[str, Any]:
    h = row.get("heading") or {}
    b = row.get("body") or {}
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "platform": row.get("platform", "web"),
        "category_id": row.get("category_id") or "",
        "heading_family": (h.get("font_family") or h.get("family") or ""),
        "body_family": (b.get("font_family") or b.get("family") or ""),
    }


def _to_font_pair_full(row: dict) -> dict[str, Any]:
    cat_name = ""
    cat = row.get("font_pair_categories")
    if isinstance(cat, dict):
        cat_name = cat.get("name_en", "")
    elif isinstance(cat, list) and cat:
        cat_name = cat[0].get("name_en", "")
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "platform": row.get("platform", "web"),
        "category_id": row.get("category_id") or "",
        "category_name": cat_name,
        "heading": _to_font_spec(row.get("heading")),
        "body": _to_font_spec(row.get("body")),
        "mono": _to_font_spec(row["mono"]) if row.get("mono") else None,
        "style_fit": row.get("style_fit") or [],
        "domain_fit": row.get("domain_fit") or [],
        "tags": row.get("mood") or [],
        "compatible_styles": row.get("style_fit") or [],
    }


def _to_domain_summary(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row.get("name_en") or row["id"],
        "category_id": row.get("category_id") or "",
        "audience": row.get("audience"),
        "tone": (row.get("tone") or [None])[0],
        "data_density": row.get("data_density"),
    }


def _to_chart_type_summary(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "data_type": row.get("data_type") or "",
        "best_chart_type": row.get("best_chart_type") or "",
        "a11y_grade": row.get("a11y_grade") or "AA",
        "library_recommendation": row.get("library_recommendation") or [],
    }


def _to_chart_type_full(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "data_type": row.get("data_type") or "",
        "keywords": row.get("keywords") or [],
        "best_chart_type": row.get("best_chart_type") or "",
        "secondary_options": row.get("secondary_options") or [],
        "when_to_use": row.get("when_to_use") or "",
        "when_not_to_use": row.get("when_not_to_use") or "",
        "data_volume_threshold": row.get("data_volume_threshold"),
        "color_guidance": row.get("color_guidance"),
        "a11y_grade": row.get("a11y_grade") or "AA",
        "a11y_notes": row.get("a11y_notes"),
        "a11y_fallback": row.get("a11y_fallback"),
        "library_recommendation": row.get("library_recommendation") or [],
        "interactive_level": row.get("interactive_level"),
    }


def _to_landing_pattern_summary(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "primary_cta_placement": row.get("primary_cta_placement") or "",
    }


def _to_landing_pattern_full(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"],
        "keywords": row.get("keywords") or [],
        "section_order": row.get("section_order") or "",
        "primary_cta_placement": row.get("primary_cta_placement") or "",
        "color_strategy": row.get("color_strategy"),
        "recommended_effects": row.get("recommended_effects"),
        "conversion_optimization": row.get("conversion_optimization"),
    }


def _to_icon_summary(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "icon_name": row.get("icon_name") or "",
        "category": row.get("category") or "",
        "library_name": row.get("library_name") or "",
        "style": row.get("style"),
    }


def _to_icon_full(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "category": row.get("category") or "",
        "icon_name": row.get("icon_name") or "",
        "keywords": row.get("keywords") or [],
        "library_id": row.get("library_id"),
        "library_name": row.get("library_name") or "",
        "import_code": row.get("import_code") or "",
        "usage": row.get("usage") or "",
        "best_for": row.get("best_for"),
        "style": row.get("style"),
    }


def _to_inspiration_page_summary(row: dict) -> dict[str, Any]:
    description = (row.get("description") or "")
    use_when = row.get("use_when")
    return {
        "id": row["id"],
        "page_type": row.get("page_type") or "",
        "appearance": row.get("appearance") or "",
        "style_family": row.get("style_family"),
        "industry": row.get("industry"),
        "mood": row.get("mood") or [],
        "keywords": (row.get("keywords") or [])[:8],
        "screenshot_path": row.get("screenshot_path") or "",
        "description": description[:240],
        "use_when": (use_when[:120] if isinstance(use_when, str) else None),
    }


def _to_inspiration_page_full(row: dict) -> dict[str, Any]:
    captured_at = row.get("captured_at")
    if captured_at is not None and not isinstance(captured_at, str):
        captured_at = str(captured_at)
    return {
        "id": row["id"],
        "source": row.get("source") or "",
        "url_guess": row.get("url_guess"),
        "captured_at": captured_at or "",
        "screenshot_path": row.get("screenshot_path") or "",

        "page_type": row.get("page_type") or "",
        "landing_pattern_id": row.get("landing_pattern_id"),
        "style_family": row.get("style_family"),
        "industry": row.get("industry"),
        "product_category": row.get("product_category"),
        "audience": row.get("audience"),
        "appearance": row.get("appearance") or "",
        "density": row.get("density"),
        "mood": row.get("mood") or [],

        "visual_signatures": row.get("visual_signatures") or [],
        "keywords": row.get("keywords") or [],
        "good_for_product_types": row.get("good_for_product_types") or [],
        "good_for_moods": row.get("good_for_moods") or [],
        "good_for_stages": row.get("good_for_stages") or [],
        "section_order": row.get("section_order") or [],

        "palette": row.get("palette") or {},
        "typography": row.get("typography") or {},
        "primary_cta": row.get("primary_cta"),
        "sections": row.get("sections") or [],
        "inspiration_metadata": row.get("inspiration_metadata") or {},
        "reference_for": row.get("reference_for") or {},
        "effects": row.get("effects") or [],
        "interaction_cues": row.get("interaction_cues") or [],
        "generation_constraints": row.get("generation_constraints"),

        "description": row.get("description") or "",
        "why_it_works": row.get("why_it_works") or "",
        "generation_prompt": row.get("generation_prompt"),
        "use_when": row.get("use_when"),
        "notes": row.get("notes"),
    }


def _to_domain_full(row: dict) -> dict[str, Any]:
    cat_name = ""
    cat = row.get("domain_categories")
    if isinstance(cat, dict):
        cat_name = cat.get("name_en", "")
    elif isinstance(cat, list) and cat:
        cat_name = cat[0].get("name_en", "")
    return {
        "id": row["id"],
        "name": row.get("name_en") or row["id"],
        "category_id": row.get("category_id") or "",
        "category_name": cat_name,
        "description": row.get("description") or "",
        "audience": row.get("audience"),
        "tone": (row.get("tone") or [None])[0],
        "data_density": row.get("data_density"),
        "ui_patterns": row.get("ui_patterns") or [],
        "examples": row.get("examples") or [],
    }
