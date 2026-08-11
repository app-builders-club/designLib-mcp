"""Validate social template staging JSON and emit a SQL data file.

Deliberately does NOT touch the database: the maintainer reviews the emitted
SQL and applies it manually (psql against the self-hosted Postgres).

Usage:
    python scripts/emit_social_templates_sql.py \
        [--staging-dir mcp-migration/social-templates/staging] \
        [--out social_templates_data.sql] \
        [--dry-run] [--upsert]

Each record is emitted as (same json_populate_record trick as export_via_rest.py,
so Postgres coerces TEXT[]/JSONB/int from the table definition):

    INSERT INTO social_templates (<cols>) SELECT <cols>
    FROM json_populate_record(NULL::social_templates, '<row-json>'::json)
    ON CONFLICT DO NOTHING;

--upsert replaces the conflict clause with DO UPDATE SET col = EXCLUDED.col
for re-applying corrected records.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STAGING = REPO_ROOT / "mcp-migration" / "social-templates" / "staging"
DEFAULT_OUT = REPO_ROOT / "social_templates_data.sql"

# created_at is intentionally absent — the DB default stamps it.
COLUMNS = (
    "id", "title", "description", "why_it_works", "content_brief",
    "format", "aspect_ratio", "appearance", "category",
    "slide_count", "min_slides", "max_slides",
    "platform_fit", "style_tags", "use_when", "keywords", "industry_fit",
    "slides", "fonts", "html_template",
    "source", "source_url", "source_note", "preview_path",
    "sort_order",
)

REQUIRED_FIELDS = (
    "id", "title", "description", "why_it_works", "content_brief",
    "format", "aspect_ratio", "appearance", "category",
    "slide_count", "min_slides", "max_slides",
    "platform_fit", "style_tags", "use_when", "keywords", "industry_fit",
    "slides", "fonts", "html_template",
)

VALID_FORMATS = {"story", "carousel"}
VALID_ASPECT_RATIOS = {"9:16", "4:5", "1:1"}
VALID_APPEARANCES = {"light", "dark", "mixed"}
VALID_CATEGORIES = {
    "promo", "product_showcase", "educational", "listicle", "checklist",
    "quote", "announcement", "testimonial", "personal_story", "before_after",
    "event", "engagement",
}
VALID_PLATFORMS = {"instagram", "tiktok", "linkedin", "facebook"}
VALID_SLIDE_ROLES = {"hook", "content", "proof", "recap", "cta"}
VALID_SLOT_TYPES = {
    "headline", "subhead", "body", "bullet_list", "cta", "kicker", "quote",
    "stat", "badge", "handle", "image_slot", "avatar_slot", "logo_slot",
}
VALID_SOURCES = {
    "canva_gallery", "adobe_express_gallery", "dribbble", "behance",
    "original", "other",
}

REQUIRED_CSS_VARS = (
    "--bg", "--surface", "--accent", "--accent-contrast",
    "--text-primary", "--text-secondary", "--font-display", "--font-body",
)

HTML_MAX_CHARS = 20_000
ID_RE = re.compile(r"^social_[a-z0-9_]+$")
SLOT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MOUSTACHE_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")
DATA_SLOT_RE = re.compile(r'data-slot="([a-z0-9_]+)"')

_ARRAY_FIELDS = ("platform_fit", "style_tags", "use_when", "keywords", "industry_fit")


def load_staging(staging_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(staging_dir.glob("*.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def validate_record(rec: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in rec]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    unknown = [f for f in rec if f not in COLUMNS]
    if unknown:
        raise ValueError(f"unknown fields: {unknown}")

    if not ID_RE.match(rec["id"]):
        raise ValueError(f"invalid id (want ^social_[a-z0-9_]+$): {rec['id']}")
    if rec["format"] not in VALID_FORMATS:
        raise ValueError(f"invalid format: {rec['format']}")
    if rec["aspect_ratio"] not in VALID_ASPECT_RATIOS:
        raise ValueError(f"invalid aspect_ratio: {rec['aspect_ratio']}")
    if rec["format"] == "story" and rec["aspect_ratio"] != "9:16":
        raise ValueError("story templates must use aspect_ratio 9:16")
    if rec["appearance"] not in VALID_APPEARANCES:
        raise ValueError(f"invalid appearance: {rec['appearance']}")
    if rec["category"] not in VALID_CATEGORIES:
        raise ValueError(f"invalid category: {rec['category']}")
    if rec.get("source", "original") not in VALID_SOURCES:
        raise ValueError(f"invalid source: {rec['source']}")

    for field in _ARRAY_FIELDS:
        values = rec[field]
        if not isinstance(values, list):
            raise ValueError(f"{field} must be a list")
        bad = [v for v in values if not isinstance(v, str) or v != v.strip().lower()]
        if bad:
            raise ValueError(f"{field} values must be lowercased strings: {bad}")
    bad_platforms = set(rec["platform_fit"]) - VALID_PLATFORMS
    if bad_platforms:
        raise ValueError(f"invalid platform_fit values: {sorted(bad_platforms)}")

    count, lo, hi = rec["slide_count"], rec["min_slides"], rec["max_slides"]
    if not (1 <= lo <= count <= hi <= 20):
        raise ValueError(f"slide bounds violated: min={lo} count={count} max={hi}")

    slides = rec["slides"]
    if not isinstance(slides, list) or len(slides) != count:
        raise ValueError(f"len(slides) must equal slide_count ({count})")
    slot_names: list[str] = []
    has_repeatable = False
    for slide in slides:
        if slide.get("role") not in VALID_SLIDE_ROLES:
            raise ValueError(f"invalid slide role: {slide.get('role')}")
        if not slide.get("layout_note"):
            raise ValueError(f"slide {slide.get('index')}: layout_note is required")
        has_repeatable = has_repeatable or bool(slide.get("repeatable"))
        for slot in slide.get("slots") or []:
            name = slot.get("name") or ""
            if not SLOT_NAME_RE.match(name):
                raise ValueError(f"invalid slot name: {name!r}")
            if slot.get("type") not in VALID_SLOT_TYPES:
                raise ValueError(f"slot {name}: invalid type {slot.get('type')}")
            slot_names.append(name)
    if len(slot_names) != len(set(slot_names)):
        dupes = sorted({n for n in slot_names if slot_names.count(n) > 1})
        raise ValueError(f"duplicate slot names: {dupes}")
    if (lo != count or hi != count) and not has_repeatable:
        raise ValueError("variable slide range requires at least one repeatable slide")

    fonts = rec["fonts"]
    if not isinstance(fonts, list) or not fonts:
        raise ValueError("fonts must be a non-empty list")
    for font in fonts:
        for key in ("role", "family", "fallback"):
            if not font.get(key):
                raise ValueError(f"font entry missing {key}: {font}")

    html = rec["html_template"]
    if len(html) > HTML_MAX_CHARS:
        raise ValueError(f"html_template too large: {len(html)} > {HTML_MAX_CHARS}")
    if "base64," in html:
        raise ValueError("html_template must not embed base64 payloads")
    if ":root" not in html:
        raise ValueError("html_template must define a :root token block")
    for var in REQUIRED_CSS_VARS:
        if not re.search(re.escape(var) + r"\s*:", html):
            raise ValueError(f"html_template :root is missing required token {var}")

    html_slots = set(MOUSTACHE_RE.findall(html)) | set(DATA_SLOT_RE.findall(html))
    declared = set(slot_names)
    if html_slots != declared:
        undeclared = sorted(html_slots - declared)
        unused = sorted(declared - html_slots)
        raise ValueError(
            f"HTML/slots mismatch: in html but not declared {undeclared}; "
            f"declared but not in html {unused}"
        )


def row_to_sql(rec: dict, upsert: bool = False) -> str:
    payload = {c: rec.get(c) for c in COLUMNS}
    payload.setdefault("source", None)
    if payload["source"] is None:
        payload["source"] = "original"
    collist = ", ".join(f'"{c}"' for c in COLUMNS)
    js = json.dumps(payload, ensure_ascii=False).replace("'", "''")
    if upsert:
        updates = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in COLUMNS if c != "id")
        conflict = f"ON CONFLICT (id) DO UPDATE SET {updates}"
    else:
        conflict = "ON CONFLICT DO NOTHING"
    return (
        f"INSERT INTO social_templates ({collist}) SELECT {collist} "
        f"FROM json_populate_record(NULL::social_templates, '{js}'::json) "
        f"{conflict};"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--staging-dir", default=str(DEFAULT_STAGING))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--upsert", action="store_true")
    args = p.parse_args()

    rows = load_staging(Path(args.staging_dir))
    print(f"Loaded {len(rows)} records from {args.staging_dir}")
    if not rows:
        print("Nothing to emit.")
        return 1

    errors = 0
    for rec in rows:
        try:
            validate_record(rec)
        except ValueError as e:
            errors += 1
            print(f"  ! {rec.get('id', '<no id>')}: {e}", file=sys.stderr)
    if errors:
        print(f"{errors} invalid record(s) — nothing written.", file=sys.stderr)
        return 1
    print("All records validated.")

    if args.dry_run:
        print("Dry run — no SQL written.")
        return 0

    rows.sort(key=lambda r: r["id"])
    for i, rec in enumerate(rows):
        rec.setdefault("sort_order", i)

    out = Path(args.out)
    with out.open("w", encoding="utf-8") as f:
        f.write("-- social_templates data (generated by scripts/emit_social_templates_sql.py)\n")
        f.write(f"-- {len(rows)} rows; apply manually: psql \"$DATABASE_URL\" -f {out.name}\n")
        f.write("BEGIN;\n\n")
        for rec in rows:
            f.write(row_to_sql(rec, upsert=args.upsert) + "\n")
        f.write("\nCOMMIT;\n")
    print(f"Wrote {len(rows)} INSERTs -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
