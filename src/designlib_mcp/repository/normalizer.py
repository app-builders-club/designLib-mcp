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
