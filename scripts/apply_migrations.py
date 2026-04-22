"""Apply SQL migrations in order using DATABASE_URL.

Usage:
    python scripts/apply_migrations.py [--dry-run]
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def discover_migrations(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.suffix == ".sql")


def apply(database_url: str, files: list[Path]) -> None:
    import psycopg

    with psycopg.connect(database_url, autocommit=False) as conn:
        for f in files:
            sql = f.read_text(encoding="utf-8")
            print(f"[apply] {f.name} ({len(sql)} bytes)")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"[ok]    {f.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    files = discover_migrations(MIGRATIONS_DIR)
    print(f"[discover] {len(files)} migrations from {MIGRATIONS_DIR}")
    for f in files:
        print(f"  - {f.name}")

    if args.dry_run:
        return 0

    apply(database_url, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
