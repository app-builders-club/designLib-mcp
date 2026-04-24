"""Ingest mcp-migration CSVs into Supabase (chart_types, landing_patterns, icons).

Usage:
    python scripts/ingest_content_catalog.py [--source-dir mcp-migration] [--dry-run]

Idempotent: uses upsert on the primary key (semantic slug).
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "mcp-migration"


def slugify(*parts: str) -> str:
    joined = "_".join(p for p in parts if p)
    slug = re.sub(r"[^a-z0-9]+", "_", joined.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def parse_keywords(raw: str) -> list[str]:
    """Split on commas and whitespace, lowercase, dedupe, drop empties."""
    tokens = re.split(r"[,\s]+", raw or "")
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        t = t.strip().lower()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_list(raw: str) -> list[str]:
    """Split on commas only — preserve multi-word items (e.g. 'Area Chart, Smooth Area')."""
    parts = (raw or "").split(",")
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _dedupe_slug(slug: str, used: set[str]) -> str:
    if slug not in used:
        used.add(slug)
        return slug
    n = 2
    while f"{slug}_{n}" in used:
        n += 1
    collided = f"{slug}_{n}"
    used.add(collided)
    print(f"  [warn] slug collision: {slug} -> {collided}", file=sys.stderr)
    return collided


def load_charts(csv_path: Path) -> list[dict]:
    used: set[str] = set()
    rows: list[dict] = []
    with csv_path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            base = f"chart_{slugify(r['Best Chart Type'].split()[0] if r['Best Chart Type'] else 'x', r['Data Type'])}"
            chart_id = _dedupe_slug(base, used)
            rows.append({
                "id": chart_id,
                "data_type": r["Data Type"].strip(),
                "keywords": parse_keywords(r["Keywords"]),
                "best_chart_type": r["Best Chart Type"].strip(),
                "secondary_options": parse_list(r["Secondary Options"]),
                "when_to_use": r["When to Use"].strip(),
                "when_not_to_use": r["When NOT to Use"].strip(),
                "data_volume_threshold": r["Data Volume Threshold"].strip() or None,
                "color_guidance": r["Color Guidance"].strip() or None,
                "a11y_grade": r["Accessibility Grade"].strip(),
                "a11y_notes": r["Accessibility Notes"].strip() or None,
                "a11y_fallback": r["A11y Fallback"].strip() or None,
                "library_recommendation": parse_list(r["Library Recommendation"]),
                "interactive_level": r["Interactive Level"].strip() or None,
                "sort_order": int(r["No"]),
            })
    return rows


def load_landing(csv_path: Path) -> list[dict]:
    used: set[str] = set()
    rows: list[dict] = []
    with csv_path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            base = f"landing_{slugify(r['Pattern Name'])}"
            pattern_id = _dedupe_slug(base, used)
            rows.append({
                "id": pattern_id,
                "name": r["Pattern Name"].strip(),
                "keywords": parse_keywords(r["Keywords"]),
                "section_order": r["Section Order"].strip(),
                "primary_cta_placement": r["Primary CTA Placement"].strip(),
                "color_strategy": r["Color Strategy"].strip() or None,
                "recommended_effects": r["Recommended Effects"].strip() or None,
                "conversion_optimization": r["Conversion Optimization"].strip() or None,
                "sort_order": int(r["No"]),
            })
    return rows


def _resolve_library_ids(client, raw_names: set[str]) -> dict[str, str]:
    """Map a CSV library label to icon_libraries.id.

    Matches case-insensitively against either the row id or the first token of
    the name (e.g. CSV 'Phosphor' or 'Phosphor (react-native)' -> id='phosphor').
    """
    resp = client.table("icon_libraries").select("id, name").execute()
    rows = resp.data or []
    by_id = {row["id"].lower(): row["id"] for row in rows}
    by_name_first = {row["name"].lower().split()[0]: row["id"] for row in rows}
    resolved: dict[str, str] = {}
    for raw in raw_names:
        key = re.sub(r"[^a-z0-9\-]+", "", raw.lower().split()[0]) if raw.split() else ""
        if not key:
            continue
        if key in by_id:
            resolved[raw] = by_id[key]
        elif key in by_name_first:
            resolved[raw] = by_name_first[key]
    return resolved


def load_icons(csv_path: Path, client=None) -> list[dict]:
    used: set[str] = set()
    raw_rows: list[dict] = []
    raw_lib_names: set[str] = set()
    with csv_path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            base = f"icon_{slugify(r['Library'].split()[0] if r['Library'] else 'lib', r['Icon Name'])}"
            icon_id = _dedupe_slug(base, used)
            raw_lib_names.add(r["Library"].strip())
            raw_rows.append({
                "id": icon_id,
                "category": r["Category"].strip(),
                "icon_name": r["Icon Name"].strip(),
                "keywords": parse_keywords(r["Keywords"]),
                "library_name": r["Library"].strip(),
                "import_code": r["Import Code"].strip(),
                "usage": r["Usage"].strip(),
                "best_for": r["Best For"].strip() or None,
                "style": r["Style"].strip() or None,
                "sort_order": int(r["No"]),
            })

    lib_map: dict[str, str] = {}
    if client is not None:
        lib_map = _resolve_library_ids(client, raw_lib_names)

    for row in raw_rows:
        row["library_id"] = lib_map.get(row["library_name"])
    return raw_rows


def _upsert(client, table: str, rows: list[dict], batch: int = 200) -> int:
    inserted = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        client.table(table).upsert(chunk, on_conflict="id").execute()
        inserted += len(chunk)
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=200)
    args = parser.parse_args()

    source = Path(args.source_dir)
    charts_csv = source / "charts.csv"
    landing_csv = source / "landing.csv"
    icons_csv = source / "icons.csv"

    for p in (charts_csv, landing_csv, icons_csv):
        if not p.exists():
            print(f"[error] missing {p}", file=sys.stderr)
            return 1

    client = None
    if not args.dry_run:
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            print("[error] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) required",
                  file=sys.stderr)
            return 1
        using_role = "service_role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anon"
        print(f"[auth] using {using_role} key for writes")
        client = create_client(url, key)

    charts = load_charts(charts_csv)
    landing = load_landing(landing_csv)
    icons = load_icons(icons_csv, client=client)

    print(f"[parsed] chart_types={len(charts)} landing_patterns={len(landing)} icons={len(icons)}")
    if args.dry_run:
        if icons:
            print(f"  [sample] icons[0]: {icons[0]['id']} lib={icons[0]['library_name']!r} "
                  f"library_id={icons[0].get('library_id')}")
        return 0

    n_charts = _upsert(client, "chart_types", charts, batch=args.batch)
    n_landing = _upsert(client, "landing_patterns", landing, batch=args.batch)
    n_icons = _upsert(client, "icons", icons, batch=args.batch)

    print(f"[ok] chart_types: {n_charts}")
    print(f"[ok] landing_patterns: {n_landing}")
    print(f"[ok] icons: {n_icons}")
    print(f"[total] {n_charts + n_landing + n_icons}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
