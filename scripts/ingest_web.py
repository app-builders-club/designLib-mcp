"""Ingest dump/db-dump/tables/*.json into Supabase with platform='web'.

Usage:
    python scripts/ingest_web.py [--dump-dir dump/db-dump/tables] [--batch 200]

Idempotent: uses upsert by primary key.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from designlib_mcp.config import Settings
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DUMP = REPO_ROOT / "dump" / "db-dump" / "tables"

WEB_TABLES = (
    "style_families",
    "domain_categories",
    "font_pair_categories",
    "domains",
    "design_styles",
    "color_palettes",
    "color_psychology",
    "font_pairs",
    "icon_libraries",
    "animation_presets",
    "animation_themed_collections",
    "background_types",
    "ui_libraries",
    "recommendation_scores",
    "app_config",
)

SKIP_TABLES = {
    "_summary",
    "profiles", "projects",
    "domain_density_mapping", "domain_tone_mapping",
    "style_family_counts",
}

PLATFORM_AWARE = {"style_families", "design_styles", "color_palettes", "font_pairs"}


def _read_table(dump_dir: Path, name: str) -> list[dict]:
    path = dump_dir / f"{name}.json"
    if not path.exists():
        print(f"  [skip] {name}.json not found", file=sys.stderr)
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _annotate_platform(table: str, rows: list[dict]) -> list[dict]:
    if table not in PLATFORM_AWARE:
        return rows
    return [{**r, "platform": "web"} for r in rows]


def _upsert(client, table: str, rows: list[dict], batch: int) -> int:
    inserted = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        client.table(table).upsert(chunk).execute()
        inserted += len(chunk)
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-dir", default=str(DEFAULT_DUMP))
    parser.add_argument("--batch", type=int, default=200)
    args = parser.parse_args()

    settings = Settings.from_env()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    dump_dir = Path(args.dump_dir)

    print(f"[ingest_web] dump_dir={dump_dir}")
    summary: dict[str, int] = {}
    for name in WEB_TABLES:
        rows = _read_table(dump_dir, name)
        rows = _annotate_platform(name, rows)
        if not rows:
            summary[name] = 0
            continue
        n = _upsert(client, name, rows, batch=args.batch)
        summary[name] = n
        print(f"  [ok] {name}: {n}")

    expected = json.loads((dump_dir / "_summary.json").read_text(encoding="utf-8"))
    print("\n[verify]")
    for name in WEB_TABLES:
        want = expected.get(name, {}).get("rows", 0)
        got = summary.get(name, 0)
        ok = "ok" if got >= want else "MISMATCH"
        print(f"  [{ok}] {name}: ingested={got} expected={want}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
