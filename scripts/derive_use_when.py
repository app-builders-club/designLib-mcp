"""Derive 1-3 sentence use_when prose for every extracted JSON file
where use_when is currently null/absent.

Format follows TODO 2 in designlib-mcp-todo.md:
  - Prose, 1-3 sentences.
  - Specifies the situational call: under which conditions is this the
    right pick over its siblings in the same triad of tag filters.

The synthesis pulls signal from inspiration_metadata.good_for_product_types,
inspiration_metadata.good_for_stages, classification.mood,
inspiration_metadata.not_recommended_for, and standout_qualities.

Usage:
    python scripts/derive_use_when.py --dry-run [--limit 5]
    python scripts/derive_use_when.py --apply
    python scripts/derive_use_when.py --apply --page-type about

--dry-run:  print samples, do not write (default)
--apply:    write use_when back into JSON files (idempotent — only fills
            nulls/absent fields)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "extracted"


_PRODUCT_LABEL = {
    "b2b_saas": "B2B SaaS",
    "consumer_app": "consumer apps",
    "ai_tool": "AI tools",
    "fintech_app": "fintech",
    "developer_tool": "developer tools",
    "data_platform": "data platforms",
    "ecommerce_fashion": "fashion ecommerce",
    "ecommerce_beauty": "beauty ecommerce",
    "ecommerce_home_goods": "home-goods ecommerce",
    "ecommerce_food_beverage": "food & beverage ecommerce",
    "editorial_publication": "editorial publications",
    "media_company": "media companies",
    "creative_agency": "creative agencies",
    "design_studio": "design studios",
    "personal_portfolio": "personal portfolios",
    "startup_generic": "early-stage startups",
    "enterprise_generic": "enterprise products",
    "healthcare": "healthcare",
    "education": "education",
    "nonprofit": "nonprofits",
    "government": "government services",
    "marketplace": "marketplaces",
    "booking_service": "booking services",
    "subscription_service": "subscription services",
    "hardware_product": "hardware products",
}

_STAGE_LABEL = {
    "hero_section": "hero",
    "whole_page": "whole page",
    "nav_only": "nav",
    "cta_band": "CTA band",
    "footer_only": "footer",
    "feature_blocks": "feature blocks",
    "typography_system": "type system",
    "color_system": "color system",
    "photography_direction": "photo direction",
    "micro_interactions": "micro-interactions",
    "empty_states": "empty states",
    "form_design": "form design",
    "data_display": "data display",
    "list_view": "list view",
}


def _humanize(slug: str) -> str:
    return slug.replace("_", " ")


_MOOD_LABEL = {
    "elegant_luxury": "elegant and luxurious",
    "playful_fun": "playful",
    "moody_dark": "moody",
    "warm_friendly": "warm and friendly",
    "calm_minimal": "calm and minimal",
    "techy_precise": "technical and precise",
    "earthy_organic": "earthy and organic",
    "retro_nostalgic": "retro and nostalgic",
    "futuristic": "futuristic",
}


def _mood(slug: str) -> str:
    return _MOOD_LABEL.get(slug, _humanize(slug))


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def derive_for_page(d: dict) -> str:
    classification = d.get("classification") or {}
    im = d.get("inspiration_metadata") or {}
    pt = classification.get("page_type") or "page"
    pt_label = pt.replace("_", " ")

    moods = classification.get("mood") or []
    gfpt = im.get("good_for_product_types") or []
    gfs = im.get("good_for_stages") or []
    not_rec = im.get("not_recommended_for") or []
    standout = im.get("standout_qualities") or []

    products = [_PRODUCT_LABEL.get(x, _humanize(x)) for x in gfpt[:3]]
    stages = [_STAGE_LABEL.get(x, _humanize(x)) for x in gfs[:3]]
    primary_mood = _mood(moods[0]) if moods else None
    secondary_mood = _mood(moods[1]) if len(moods) > 1 else None

    # Sentence 1 — when to reach for it.
    audience_clause = _join(products) if products else f"{pt_label} work"
    if primary_mood and secondary_mood and primary_mood != secondary_mood:
        mood_clause = f"the brand wants to read as {primary_mood} and {secondary_mood}"
    elif primary_mood:
        mood_clause = f"the brand wants to read as {primary_mood}"
    else:
        mood_clause = "the brand has a clear point of view it wants to commit to"

    if stages:
        stage_clause = _join(stages)
        s1 = (
            f"Use when designing for {audience_clause} and {mood_clause} — "
            f"the strongest borrowable layer is the {stage_clause}."
        )
    else:
        s1 = f"Use when designing for {audience_clause} and {mood_clause}."

    # Sentence 2 — what makes it the right pick over siblings.
    if standout:
        s2_qual = _humanize(standout[0])
        s2 = (
            f"Pick this over similar references when you specifically want the {s2_qual} — "
            f"that's the move that separates this page from its sibling candidates."
        )
    else:
        s2 = ""

    # Sentence 3 — when not to use it. Reuse the product-label table so
    # "consumer_app" becomes "consumer apps", not "consumer app".
    if not_rec:
        raw = not_rec[0]
        nr_label = _PRODUCT_LABEL.get(raw, _humanize(raw))
        s3 = f"Avoid for {nr_label}, where the gesture won't transfer."
    else:
        s3 = ""

    parts = [p for p in (s1, s2, s3) if p]
    return " ".join(parts)


def _iter_targets(source: Path, page_type: str | None) -> list[Path]:
    files = sorted(source.glob("*/*.json"))
    out: list[Path] = []
    for fp in files:
        try:
            with fp.open(encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        pt = d.get("classification", {}).get("page_type")
        if page_type and pt != page_type:
            continue
        if d.get("use_when"):
            continue
        out.append(fp)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True,
                       help="Print samples; do not write (default)")
    group.add_argument("--apply", action="store_true",
                       help="Write use_when back into JSON files")
    parser.add_argument("--limit", type=int, default=5,
                        help="Sample size for --dry-run (default: 5)")
    parser.add_argument("--page-type", default=None,
                        help="Restrict to a single page_type")
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.exists():
        print(f"[error] {source} not found", file=sys.stderr)
        return 1

    targets = _iter_targets(source, args.page_type)
    print(f"[scan] {len(targets)} JSON files need use_when")
    if args.page_type:
        print(f"       (filtered to page_type={args.page_type})")
    if not targets:
        return 0

    apply_mode = args.apply
    samples = targets if apply_mode else targets[: args.limit]

    written = 0
    for fp in samples:
        with fp.open(encoding="utf-8") as fh:
            d = json.load(fh)
        seed = derive_for_page(d)
        if apply_mode:
            d["use_when"] = seed
            with fp.open("w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            written += 1
        else:
            print()
            print(f"--- {fp.relative_to(REPO_ROOT)} ({d.get('classification', {}).get('page_type')})")
            print(seed)

    if apply_mode:
        print(f"[done] wrote use_when into {written} files")
    else:
        print(f"\n[dry-run] showed {len(samples)} of {len(targets)} candidates "
              f"(use --apply to write back to all of them)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
