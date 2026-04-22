"""Ingest iOS data (medians + definitions + raw aggregated profiles) into Supabase.

Usage:
    python scripts/ingest_ios.py [--reset]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from designlib_mcp.config import Settings
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
EXTRACTION_DIR = REPO_ROOT / "extraction"

IOS_FONT_PAIRS: list[dict] = [
    {
        "id": "ios_sf_pro_text_display",
        "name": "SF Pro Text + SF Pro Display",
        "category_id": "system_sans",
        "heading": {"font_family": "SF Pro Display", "weights": [400, 600, 700], "is_system_font": True},
        "body":    {"font_family": "SF Pro Text",    "weights": [400, 500, 600], "is_system_font": True},
        "mono": None,
        "import_url": "", "size_kb": 0, "variable_font": True,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["neutral", "system"], "use_cases": ["default_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
    {
        "id": "ios_sf_pro_text_new_york",
        "name": "SF Pro Text + New York Serif",
        "category_id": "system_serif_mix",
        "heading": {"font_family": "New York", "weights": [400, 600, 700], "is_system_font": True},
        "body":    {"font_family": "SF Pro Text", "weights": [400, 500], "is_system_font": True},
        "mono": None,
        "import_url": "", "size_kb": 0, "variable_font": False,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["editorial"], "use_cases": ["editorial_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
    {
        "id": "ios_sf_pro_rounded",
        "name": "SF Pro Rounded (heading + body)",
        "category_id": "system_rounded",
        "heading": {"font_family": "SF Pro Rounded", "weights": [500, 700], "is_system_font": True},
        "body":    {"font_family": "SF Pro Rounded", "weights": [400, 500], "is_system_font": True},
        "mono": None,
        "import_url": "", "size_kb": 0, "variable_font": True,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["friendly", "playful"], "use_cases": ["youthful_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
    {
        "id": "ios_sf_pro_text_custom_serif",
        "name": "SF Pro Text + Custom Serif",
        "category_id": "system_custom_serif",
        "heading": {"font_family": "Custom Serif", "weights": [400, 700], "is_system_font": False},
        "body":    {"font_family": "SF Pro Text",  "weights": [400, 500], "is_system_font": True},
        "mono": None,
        "import_url": "", "size_kb": 0, "variable_font": False,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["editorial", "branded"], "use_cases": ["branded_editorial_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
    {
        "id": "ios_sf_pro_text_custom_sans",
        "name": "SF Pro Text + Custom Sans",
        "category_id": "system_custom_sans",
        "heading": {"font_family": "Custom Sans", "weights": [500, 700], "is_system_font": False},
        "body":    {"font_family": "SF Pro Text", "weights": [400, 500], "is_system_font": True},
        "mono": None,
        "import_url": "", "size_kb": 0, "variable_font": False,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["branded"], "use_cases": ["branded_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
    {
        "id": "ios_sf_mono_display",
        "name": "SF Mono + SF Pro Display",
        "category_id": "system_mono_mix",
        "heading": {"font_family": "SF Pro Display", "weights": [600, 700], "is_system_font": True},
        "body":    {"font_family": "SF Mono",        "weights": [400, 500], "is_system_font": True},
        "mono":    {"font_family": "SF Mono",        "weights": [400, 500], "is_system_font": True},
        "import_url": "", "size_kb": 0, "variable_font": False,
        "line_heights": {}, "letter_spacing": {},
        "mood": ["technical"], "use_cases": ["data_dense_ios"],
        "style_fit": [], "domain_fit": [], "used_by": [],
        "platform": "ios",
    },
]


def build_style_family_row(family_slug: str, defn: dict, sort_order: int) -> dict:
    return {
        "id": family_slug,
        "name_en": defn["name_en"],
        "description": defn["description"],
        "sort_order": sort_order,
        "platform": "ios",
    }


def build_design_style_row(family_slug: str, defn: dict, medians: dict) -> dict:
    light = medians.get("palette_light") or {}
    dark = medians.get("palette_dark")
    appearance_support = ["light"] + (["dark"] if dark else [])
    typo = medians.get("typography") or {}
    layout = medians.get("layout") or {}
    lg = medians.get("liquid_glass") or {}
    return {
        "id": f"{family_slug}_ios",
        "family_id": family_slug,
        "name_en": defn["name_en"],
        "description": defn["description"],
        "visual_signatures": defn.get("visual_signatures", []),
        "emotional_keywords": defn.get("emotional_keywords", []),
        "anti_patterns": defn.get("anti_patterns", []),
        "tokens": {
            "colors": {
                "background": light.get("background"),
                "surface": light.get("surface_card") or light.get("background"),
                "border": light.get("separator"),
                "text_primary": light.get("text_primary"),
                "text_secondary": light.get("text_secondary"),
                "primary": light.get("accent_primary"),
            },
            "typography": {
                "heading_font": typo.get("heading_classification"),
                "body_font": typo.get("body_classification"),
                "mono_font": "SF Mono" if typo.get("mono_present") else None,
            },
            "layout": {
                "density": layout.get("density_typical"),
                "corner_radius_card_px": (
                    int(layout["corner_radius_cards_pt_median"])
                    if layout.get("corner_radius_cards_pt_median") is not None else None
                ),
            },
        },
        "reference_products": [],
        "domain_fit": {},
        "platform": "ios",
        "ios_metadata": {
            "liquid_glass_posture": lg.get("posture", "unclear"),
            "surfaces_affected": lg.get("surfaces_affected", []),
            "list_style_dominant": layout.get("list_style_dominant"),
            "density_typical": layout.get("density_typical"),
            "appearance_support": appearance_support,
            "corner_radius_cards_pt_median": layout.get("corner_radius_cards_pt_median"),
            "iconography": medians.get("iconography") or "unclear",
            "reference_apps": medians.get("reference_apps", []),
        },
    }


def _palette_colors_jsonb(pal: dict) -> dict:
    return {role: hex_v for role, hex_v in pal.items() if hex_v}


def build_palette_rows(family_slug: str, family_name: str, medians: dict) -> list[dict]:
    rows: list[dict] = []
    light = medians.get("palette_light")
    if light:
        rows.append({
            "id": f"{family_slug}_ios_light",
            "palette_type": "collection",
            "family_id": family_slug,
            "name": f"{family_name} (iOS Light)",
            "colors": _palette_colors_jsonb(light),
            "tags": ["ios_aggregated", "light"],
            "style_fit": [f"{family_slug}_ios"],
            "wcag_aa": None,
            "dark_mode_first": False,
            "sort_order": 0,
            "platform": "ios",
        })
    dark = medians.get("palette_dark")
    if dark:
        rows.append({
            "id": f"{family_slug}_ios_dark",
            "palette_type": "collection",
            "family_id": family_slug,
            "name": f"{family_name} (iOS Dark)",
            "colors": _palette_colors_jsonb(dark),
            "tags": ["ios_aggregated", "dark"],
            "style_fit": [f"{family_slug}_ios"],
            "wcag_aa": None,
            "dark_mode_first": True,
            "sort_order": 1,
            "platform": "ios",
        })
    return rows


def build_app_profile_rows(extraction_dir: Path, family_assignments: list[dict]) -> list[dict]:
    by_slug = {row["slug"]: row for row in family_assignments}
    rows: list[dict] = []
    for f in (extraction_dir / "aggregated").glob("*.json"):
        agg = json.loads(f.read_text(encoding="utf-8"))
        slug = agg["slug"]
        assignment = by_slug.get(slug, {})
        rows.append({
            "slug": slug,
            "family_id": assignment.get("family_assigned"),
            "aggregated": agg,
            "screenshot_count": agg.get("screenshot_count"),
            "confidence": assignment.get("confidence"),
        })
    return rows


def _reset_ios(client) -> None:
    print("[reset] removing ios rows...")
    client.table("ios_app_profiles").delete().neq("slug", "").execute()
    client.table("color_palettes").delete().eq("platform", "ios").execute()
    client.table("font_pairs").delete().eq("platform", "ios").execute()
    client.table("design_styles").delete().eq("platform", "ios").execute()
    client.table("style_families").delete().eq("platform", "ios").execute()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="delete existing ios rows before ingest")
    args = parser.parse_args()

    settings = Settings.from_env()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    medians = json.loads((DATA_DIR / "ios_family_medians.json").read_text(encoding="utf-8"))
    definitions = json.loads((DATA_DIR / "ios_family_definitions.json").read_text(encoding="utf-8"))
    family_assignments = json.loads((EXTRACTION_DIR / "family_assignments.json").read_text(encoding="utf-8"))["assignments"]

    if args.reset:
        _reset_ios(client)

    fam_rows = [
        build_style_family_row(slug, definitions[slug], sort_order=100 + i)
        for i, slug in enumerate(definitions)
    ]
    client.table("style_families").upsert(fam_rows).execute()
    print(f"[ok] style_families: {len(fam_rows)}")

    style_rows = [
        build_design_style_row(slug, definitions[slug], medians[slug])
        for slug in definitions if slug in medians
    ]
    client.table("design_styles").upsert(style_rows).execute()
    print(f"[ok] design_styles: {len(style_rows)}")

    palette_rows: list[dict] = []
    for slug, defn in definitions.items():
        if slug in medians:
            palette_rows.extend(build_palette_rows(slug, defn["name_en"], medians[slug]))
    client.table("color_palettes").upsert(palette_rows).execute()
    print(f"[ok] color_palettes: {len(palette_rows)}")

    # 4a. font_pair_categories — ensure iOS categories exist (FK target).
    ios_font_pair_categories = [
        {"id": "system_sans",         "name_en": "System Sans (iOS)",
         "description": "SF Pro Text/Display combinations.",       "sort_order": 100},
        {"id": "system_serif_mix",    "name_en": "System Serif Mix (iOS)",
         "description": "SF Pro paired with New York serif.",      "sort_order": 101},
        {"id": "system_rounded",      "name_en": "System Rounded (iOS)",
         "description": "SF Pro Rounded for friendly UI.",         "sort_order": 102},
        {"id": "system_custom_serif", "name_en": "System + Custom Serif (iOS)",
         "description": "SF Pro body with branded serif heading.", "sort_order": 103},
        {"id": "system_custom_sans",  "name_en": "System + Custom Sans (iOS)",
         "description": "SF Pro body with branded sans heading.",  "sort_order": 104},
        {"id": "system_mono_mix",     "name_en": "System Mono Mix (iOS)",
         "description": "SF Mono paired with SF Pro Display.",     "sort_order": 105},
    ]
    client.table("font_pair_categories").upsert(ios_font_pair_categories).execute()
    print(f"[ok] font_pair_categories (ios): {len(ios_font_pair_categories)}")

    # 4b. font_pairs (canonical iOS combinations)
    client.table("font_pairs").upsert(IOS_FONT_PAIRS).execute()
    print(f"[ok] font_pairs: {len(IOS_FONT_PAIRS)}")

    profile_rows = build_app_profile_rows(EXTRACTION_DIR, family_assignments)
    client.table("ios_app_profiles").upsert(profile_rows).execute()
    print(f"[ok] ios_app_profiles: {len(profile_rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
