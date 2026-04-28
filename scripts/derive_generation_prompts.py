"""Derive 2-4 sentence generation_prompt seeds for non-landing/signup
extracted JSON files where generation_prompt is currently null.

Format follows TODO 1 in designlib-mcp-todo.md:
  1. Structural posture (specific to this page)
  2. Load-bearing element (the thing that, removed, collapses the design)
  3. Risk being taken vs. a generic version of the page_type
  4. Optionally: what to avoid copying

The output is a starting-point seed — synthesized from existing structured
fields (section_order, inspiration_metadata.standout_qualities,
palette_strategy, style_family, mood, not_recommended_for, description,
why_it_works). It is NOT screenshot-aware; treat it as a usable baseline
that can be hand-edited or replaced with an LLM-generated version.

Usage:
    python scripts/derive_generation_prompts.py --dry-run [--limit 5]
    python scripts/derive_generation_prompts.py --apply
    python scripts/derive_generation_prompts.py --apply --page-type pricing

--dry-run:  validate inputs, print samples, do not write
--apply:    write generation_prompt back into JSON files (idempotent;
            only fills nulls — does not overwrite existing prompts)
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "extracted"
TARGET_PAGE_TYPES = {
    "about", "blog_index", "blog_post", "careers", "ecommerce_home",
    "portfolio", "pricing", "product_listing", "product_page",
}


# ---------------------------------------------------------------------------
# Synthesis — turn structured fields into a 2-4 sentence prose seed.
# ---------------------------------------------------------------------------

_SECTION_POSTURE = {
    # opening section -> short posture phrase fragment
    "nav_top_split": "thin split nav above",
    "nav_top_centered": "centered nav above",
    "nav_minimal_logo_only": "near-invisible nav above",
    "hero_centered_above_image": "a centered hero stacked above its media",
    "hero_split_left_copy_right_image": "a split hero with copy left and image right",
    "hero_split_right_copy_left_image": "a split hero with image left and copy right",
    "hero_fullbleed_video": "a full-bleed video hero",
    "hero_gradient_text_only": "a type-only gradient hero",
    "hero_stacked_cta": "a stacked hero with CTA below the fold mark",
    "hero_editorial_image_overlay": "an editorial photo hero with overlaid type",
    "hero_minimal_type_only": "a minimal type-only opening",
    "hero_with_background_illustration": "a hero with illustrated background",
    "about_mission_statement": "a quiet mission statement",
    "article_hero": "an article hero with byline and meta",
    "blog_index_grid_3col": "a 3-column post grid",
    "blog_index_list_compact": "a compact list of posts",
    "blog_index_featured_plus_grid": "a featured-post-plus-grid opening",
    "careers_mission": "a careers mission opener",
    "ecom_hero_editorial": "an editorial ecommerce hero",
    "portfolio_work_grid": "a work grid",
    "portfolio_work_list_scroll": "a scrolling list of work",
    "pricing_three_tier": "a three-tier pricing table",
    "pricing_toggle_monthly_annual": "pricing with a monthly/annual toggle",
    "pricing_single_focused": "a single-focused price card",
    "pricing_comparison_table": "a comparison table",
    "plist_filter_sidebar_grid": "a filter sidebar paired with a product grid",
    "plist_filter_top_bar_grid": "a top-bar filter above a product grid",
    "plist_category_hero": "a category hero",
    "pdp_gallery_sticky_left_info_right": "a sticky gallery on the left with info on the right",
    "pdp_gallery_top_info_below": "a gallery above with info below",
    "pdp_gallery_fullbleed_info_overlay": "a full-bleed gallery with overlaid info",
    "signup_form_centered": "a centered signup form",
    "signup_split_form_illustration": "a signup form split with illustration",
    "signup_split_form_photo": "a signup form split with photography",
}

_SCROLL_LENGTH = {
    "very_short": "compact",
    "short": "compact",
    "medium": "mid-length",
    "long": "long-scroll",
    "very_long": "long-scroll editorial",
}


def _scroll_descriptor(section_count: int) -> str:
    if section_count <= 4:
        return "compact"
    if section_count <= 7:
        return "mid-length"
    if section_count <= 10:
        return "long-scroll"
    return "long-scroll editorial"


def _section_after_hero(section_order: list[str]) -> str | None:
    """Return a short phrase for the first non-nav, non-hero section."""
    skip_prefixes = ("nav_", "hero_")
    for s in section_order:
        if s.startswith(skip_prefixes):
            continue
        if s in _SECTION_POSTURE:
            return _SECTION_POSTURE[s]
        return s.replace("_", " ")
    return None


def _slug_to_phrase(slug: str) -> str:
    """Turn a snake_case slug like 'cream_surface_with_single_violet_accent'
    into a readable phrase 'cream surface with a single violet accent'.

    Article insertion only fires mid-phrase ("with single ..." → "with a single
    ...") so the caller can prepend its own article on the leading word without
    producing "the an oversized ...".
    """
    if not slug:
        return ""
    s = slug.replace("_", " ").strip()
    # Light articles for readability — keep cheap (no full NLP). Anchor on a
    # preceding preposition so we don't double-article the leading word.
    s = re.sub(r"\b(with|of|on|in|by|for)\s+single\b", r"\1 a single", s)
    s = re.sub(r"\b(with|of|on|in|by|for)\s+oversized\b", r"\1 an oversized", s)
    s = re.sub(r"\b(with|of|on|in|by|for)\s+abstract\b", r"\1 an abstract", s)
    return s


def _article(word: str) -> str:
    """Pick 'a' / 'an' for `word` based on its leading sound — vowel sounds
    take 'an'. Cheap heuristic; good enough for the slugified inputs we feed in."""
    if not word:
        return "a"
    return "an" if word[0].lower() in "aeiou" else "a"


def _humanize_style(style_family: str | None) -> str | None:
    if not style_family:
        return None
    return style_family.replace("_", " ")


def _humanize_palette_strategy(strategy: str | None) -> str | None:
    if not strategy:
        return None
    return strategy.replace("_", " ")


_NOT_REC_LABEL = {
    "b2b_saas": "B2B SaaS",
    "consumer_app": "consumer apps",
    "ai_tool": "AI tools",
    "fintech_app": "fintech",
    "developer_tool": "developer tools",
    "data_platform": "data platforms",
    "ecommerce_fashion": "fashion ecommerce",
    "ecommerce_beauty": "beauty ecommerce",
    "ecommerce_home_goods": "home-goods ecommerce",
    "editorial_publication": "editorial publications",
    "media_company": "media companies",
    "creative_agency": "creative agencies",
    "design_studio": "design studios",
    "personal_portfolio": "personal portfolios",
    "startup_generic": "early-stage startups",
    "enterprise_generic": "enterprise products",
    "marketplace": "marketplaces",
    "booking_service": "booking services",
    "subscription_service": "subscription services",
    "hardware_product": "hardware products",
}


_MOOD_PROSE = {
    "elegant_luxury": "elegant-luxury",
    "playful_fun": "playful",
    "moody_dark": "moody",
    "warm_friendly": "warm",
    "calm_minimal": "calm-minimal",
    "techy_precise": "techy",
    "earthy_organic": "earthy",
    "retro_nostalgic": "retro",
    "futuristic": "futuristic",
}


def _humanize_not_recommended(item: str | None) -> str | None:
    if not item:
        return None
    return _NOT_REC_LABEL.get(item, item.replace("_", " "))


def _humanize_mood(mood: str | None) -> str | None:
    if not mood:
        return None
    return _MOOD_PROSE.get(mood, mood.replace("_", " "))


_PAGE_TYPE_GENERIC_RISK = {
    "about": "boilerplate-team-and-mission slab",
    "pricing": "feature-checklist-grid that tells the visitor nothing about who it's for",
    "portfolio": "uniform thumbnail grid of indistinct work",
    "blog_index": "Medium-clone post list",
    "blog_post": "centered article column with no editorial point of view",
    "careers": "perks-and-benefits slab",
    "product_listing": "navigation-hostile uniform card grid",
    "product_page": "spec-sheet-and-add-to-cart layout",
    "ecommerce_home": "category-tile-and-promo-banner grid",
}


_FIRST_SENTENCE = re.compile(r"^([^.!?]+[.!?])")


def _first_sentence(text: str) -> str:
    if not text:
        return ""
    m = _FIRST_SENTENCE.search(text.strip())
    if m:
        return m.group(1).strip()
    return text.strip()


def derive_for_page(d: dict) -> str:
    """Synthesize a 2-4 sentence generation_prompt seed from existing fields."""
    pt = d.get("classification", {}).get("page_type") or "page"
    pt_label = pt.replace("_", " ")
    section_order = d.get("section_order") or []
    standout = (d.get("inspiration_metadata") or {}).get("standout_qualities") or []
    not_rec = (d.get("inspiration_metadata") or {}).get("not_recommended_for") or []
    classification = d.get("classification") or {}
    palette = d.get("palette") or {}
    mood = classification.get("mood") or []

    # Sentence 1 — structural posture.
    scroll = _scroll_descriptor(len(section_order))
    art = _article(scroll).capitalize()
    after_hero = _section_after_hero(section_order)
    if after_hero:
        s1 = (
            f"{art} {scroll} {pt_label} that opens with {after_hero} "
            f"and runs {len(section_order)} sections deep."
        )
    else:
        s1 = f"{art} {scroll} {pt_label} with {len(section_order)} sections."

    # Sentence 2 — load-bearing element.
    if standout:
        load_bearing = _slug_to_phrase(standout[0])
        # Drop the leading "the" when the phrase already opens with its own
        # article (e.g. "an oversized year numerals timeline") to avoid
        # "the an oversized ...".
        determiner = "" if re.match(r"^(a|an|the)\s", load_bearing) else "the "
        s2 = (
            f"The load-bearing move is {determiner}{load_bearing}; "
            f"strip that out and the page collapses into a generic {pt_label}."
        )
    else:
        # Fallback: derive from why_it_works first sentence.
        why = _first_sentence(d.get("why_it_works") or "")
        s2 = why or (
            f"What makes it work is the way it commits to a single visual posture "
            f"instead of hedging with neutral defaults."
        )

    # Sentence 3 — risk vs. generic version.
    style = _humanize_style(classification.get("style_family"))
    pal = _humanize_palette_strategy(palette.get("palette_strategy"))
    generic = _PAGE_TYPE_GENERIC_RISK.get(pt, f"generic {pt_label}")
    primary_mood = _humanize_mood(mood[0]) if mood else None
    bits = []
    if style:
        bits.append(f"{_article(style)} {style} register")
    if pal:
        bits.append(f"{_article(pal)} {pal} palette")
    if primary_mood:
        bits.append(f"{_article(primary_mood)} {primary_mood} mood")
    if bits:
        joined = ", ".join(bits[:-1]) + (" and " + bits[-1] if len(bits) > 1 else bits[0])
        s3 = (
            f"It bets on {joined} — the upside vs. a {generic} is conviction; "
            f"the downside if it isn't earned is preciousness."
        )
    else:
        s3 = (
            f"It chooses commitment over hedging — the upside vs. a {generic} "
            f"is conviction; the downside if it isn't earned is preciousness."
        )

    # Sentence 4 (optional) — what to avoid copying.
    if not_rec:
        avoid_label = _humanize_not_recommended(not_rec[0])
        s4 = (
            f"Don't transplant the surface treatment to {avoid_label} — "
            f"the gesture only reads where the brand is already aligned with this register."
        )
        return f"{s1} {s2} {s3} {s4}"

    return f"{s1} {s2} {s3}"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

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
        if pt not in TARGET_PAGE_TYPES:
            continue
        if page_type and pt != page_type:
            continue
        if d.get("generation_prompt"):
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
                       help="Write generation_prompt back into JSON files")
    parser.add_argument("--limit", type=int, default=5,
                        help="Sample size for --dry-run (default: 5)")
    parser.add_argument("--page-type", default=None,
                        help="Restrict to a single page_type (e.g. pricing)")
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.exists():
        print(f"[error] {source} not found", file=sys.stderr)
        return 1

    targets = _iter_targets(source, args.page_type)
    print(f"[scan] {len(targets)} JSON files need generation_prompt")
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
            d["generation_prompt"] = seed
            with fp.open("w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            written += 1
        else:
            print()
            print(f"--- {fp.relative_to(REPO_ROOT)} ({d.get('classification', {}).get('page_type')})")
            print(seed)

    if apply_mode:
        print(f"[done] wrote generation_prompt into {written} files")
    else:
        print(f"\n[dry-run] showed {len(samples)} of {len(targets)} candidates "
              f"(use --apply to write back to all of them)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
