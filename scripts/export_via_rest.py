"""Export all designlib catalog tables from Supabase via the REST API.

Path-B migration helper (no database password required): pulls every row
through PostgREST using the service_role key (bypasses RLS) and writes a
self-contained SQL file that loads into a plain self-hosted Postgres.

Each row is emitted as:

    INSERT INTO <table> (<cols>) SELECT <cols>
    FROM json_populate_record(NULL::<table>, '<row-json>'::json)
    ON CONFLICT DO NOTHING;

Using json_populate_record lets Postgres coerce JSON -> column types
(TEXT[], JSONB, int, bool, timestamptz) from the table definition, so we
never have to format array / jsonb literals by hand.

Usage (from repo root, with .venv active):

    python scripts/export_via_rest.py
    # -> writes designlib_data.sql in the repo root

Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from .env / environment.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

# Tables in FK-safe load order (parents before children).
TABLES: list[str] = [
    "style_families",
    "domain_categories",
    "font_pair_categories",
    "icon_libraries",
    "domains",
    "design_styles",
    "color_palettes",
    "color_psychology",
    "font_pairs",
    "ios_app_profiles",
    "animation_presets",
    "animation_themed_collections",
    "background_types",
    "ui_libraries",
    "recommendation_scores",
    "app_config",
    "chart_types",
    "landing_patterns",
    "icons",
    "inspiration_pages",
    "animations",
]

# Columns to drop per table (e.g. GENERATED ALWAYS identity — let it regenerate).
EXCLUDE_COLS: dict[str, set[str]] = {
    "recommendation_scores": {"id"},
}

PAGE = 1000
OUTPUT = "designlib_data.sql"


def fetch_all(base: str, key: str, table: str) -> list[dict]:
    """Page through a PostgREST table and return all rows."""
    rows: list[dict] = []
    offset = 0
    while True:
        url = f"{base}/rest/v1/{table}?select=*&limit={PAGE}&offset={offset}"
        req = urllib.request.Request(url, headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            print(f"  ! {table}: HTTP {e.code} — {body[:200]}", file=sys.stderr)
            return rows
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
    return rows


def row_to_sql(table: str, row: dict) -> str:
    cols = [c for c in row.keys() if c not in EXCLUDE_COLS.get(table, set())]
    collist = ", ".join(f'"{c}"' for c in cols)
    payload = {c: row[c] for c in cols}
    js = json.dumps(payload, ensure_ascii=False).replace("'", "''")
    return (
        f"INSERT INTO {table} ({collist}) SELECT {collist} "
        f"FROM json_populate_record(NULL::{table}, '{js}'::json) "
        f"ON CONFLICT DO NOTHING;"
    )


def main() -> None:
    load_dotenv()
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not key:
        sys.exit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required in .env")

    total = 0
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("-- designlib data export via PostgREST (path B, no DB password)\n")
        f.write("BEGIN;\n\n")
        for table in TABLES:
            rows = fetch_all(base, key, table)
            print(f"  {table}: {len(rows)} rows")
            total += len(rows)
            if not rows:
                continue
            f.write(f"-- {table} ({len(rows)} rows)\n")
            for row in rows:
                f.write(row_to_sql(table, row) + "\n")
            f.write("\n")
        f.write("COMMIT;\n")

    print(f"\nDone. {total} rows across {len(TABLES)} tables -> {OUTPUT}")


if __name__ == "__main__":
    main()
