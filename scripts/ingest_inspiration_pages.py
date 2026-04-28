"""Ingest extracted/<category>/*.json into Supabase inspiration_pages.

Re-validates each file against PAGE_ANALYSIS_PROMPT.md rules using validate_extracted.py;
only files that pass are upserted. Failed files are listed and skipped.

Usage:
    python scripts/ingest_inspiration_pages.py [--source-dir extracted] [--dry-run] [--strict]

Idempotent: upsert by id (semantic slug "page_<...>").
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "extracted"
VALIDATOR_PATH = Path(__file__).resolve().parent / "validate_extracted.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_extracted", VALIDATOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _validate_one(mod, fp: Path) -> list[str]:
    """Return list of issue strings; empty list = OK. Mirrors validate_extracted.py logic."""
    try:
        with fp.open(encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as e:
        return [f"PARSE-FAIL: {e}"]

    issues: list[str] = []
    pt = d.get("classification", {}).get("page_type")
    if pt not in mod.VALID_PAGE_TYPES:
        issues.append(f"page_type {pt!r} not in vocab")
    lpid = d.get("classification", {}).get("landing_pattern_id")
    if pt == "marketing_landing":
        if not lpid:
            issues.append("landing_pattern_id null on marketing_landing")
    else:
        if lpid:
            issues.append(f"landing_pattern_id set on non-landing ({pt})")

    so = d.get("section_order") or []
    secs = d.get("sections") or []
    if len(so) != len(secs):
        issues.append(f"section_order/sections length mismatch ({len(so)} vs {len(secs)})")
    for i, (a, b) in enumerate(zip(so, [s.get("type") for s in secs])):
        if a != b:
            issues.append(f"section_order[{i}]={a!r} vs sections[{i}].type={b!r}")
    for s in secs:
        if s.get("type") not in mod.VALID_SECTIONS:
            issues.append(f"unknown section type: {s.get('type')!r}")

    for sig in d.get("visual_signatures") or []:
        if sig not in mod.VALID_SIGS:
            issues.append(f"unknown visual_signature: {sig!r}")

    moods = d.get("classification", {}).get("mood") or []
    if not (2 <= len(moods) <= 6):
        issues.append(f"classification.mood count {len(moods)} not in 2..6")
    for m in moods:
        if m not in mod.VALID_MOODS:
            issues.append(f"unknown mood: {m!r}")

    im = d.get("inspiration_metadata", {})
    gpt = im.get("good_for_product_types") or []
    if not (2 <= len(gpt) <= 6):
        issues.append(f"good_for_product_types count {len(gpt)} not in 2..6")
    for x in gpt:
        if x not in mod.VALID_PRODUCT_TYPES:
            issues.append(f"unknown product_type: {x!r}")
    gm = im.get("good_for_moods") or []
    if not (2 <= len(gm) <= 6):
        issues.append(f"good_for_moods count {len(gm)} not in 2..6")
    for x in gm:
        if x not in mod.VALID_MOODS:
            issues.append(f"unknown im.mood: {x!r}")
    gs = im.get("good_for_stages") or []
    if not (1 <= len(gs) <= 5):
        issues.append(f"good_for_stages count {len(gs)} not in 1..5")
    for x in gs:
        if x not in mod.VALID_STAGES:
            issues.append(f"unknown stage: {x!r}")

    kws = d.get("keywords") or []
    if not (8 <= len(kws) <= 20):
        issues.append(f"keywords count {len(kws)} not in 8..20")

    gp = d.get("generation_prompt"); gc = d.get("generation_constraints")
    if pt in ("marketing_landing", "signup"):
        if not gp:
            issues.append("generation_prompt null on landing/signup")
        if not gc:
            issues.append("generation_constraints null on landing/signup")
    else:
        # Since migration 007 generation_prompt is allowed for any page_type;
        # only generation_constraints stays gated to landing/signup.
        if gc is not None:
            issues.append("generation_constraints non-null on non-landing/signup")
    if gp is not None and not isinstance(gp, str):
        issues.append("generation_prompt is not a string")

    uw = d.get("use_when")
    if uw is not None and not isinstance(uw, str):
        issues.append("use_when is not a string")

    role_intent = d.get("palette", {}).get("role_intent", {}) or {}
    for k, v in role_intent.items():
        if isinstance(v, str) and v.upper() in ("#FFFFFF", "#000000"):
            issues.append(f"pure {v} in role_intent.{k}")

    for path, val in mod.find_section_strings(d.get("sections", [])):
        if mod.HEX.search(val):
            issues.append(f"hex inside sections at {path}: {val!r}")

    issues += mod.scan_for_size_adj(d)
    return issues


def _to_row(d: dict) -> dict:
    """Flatten extracted JSON into an inspiration_pages row."""
    cls = d.get("classification", {})
    im = d.get("inspiration_metadata", {})
    return {
        "id":                    d["id"],
        "source":                d["source"],
        "url_guess":             d.get("url_guess"),
        "captured_at":           d["captured_at"],
        "screenshot_path":       d["screenshot_path"],

        "page_type":             cls["page_type"],
        "landing_pattern_id":    cls.get("landing_pattern_id"),
        "style_family":          cls.get("style_family"),
        "industry":              cls.get("industry"),
        "product_category":      cls.get("product_category"),
        "audience":              cls.get("audience"),
        "appearance":            cls["appearance"],
        "density":               cls.get("density"),
        "mood":                  cls.get("mood") or [],

        "visual_signatures":        d.get("visual_signatures") or [],
        "keywords":                 d.get("keywords") or [],
        "good_for_product_types":   im.get("good_for_product_types") or [],
        "good_for_moods":           im.get("good_for_moods") or [],
        "good_for_stages":          im.get("good_for_stages") or [],
        "section_order":            d.get("section_order") or [],

        "palette":                  d.get("palette") or {},
        "typography":               d.get("typography") or {},
        "primary_cta":              d.get("primary_cta"),
        "sections":                 d.get("sections") or [],
        "inspiration_metadata":     im,
        "reference_for":            d.get("reference_for") or {},
        "effects":                  d.get("effects") or [],
        "interaction_cues":         d.get("interaction_cues") or [],
        "generation_constraints":   d.get("generation_constraints"),

        "description":              d["description"],
        "why_it_works":             d["why_it_works"],
        "generation_prompt":        d.get("generation_prompt"),
        "use_when":                 d.get("use_when"),
        "notes":                    d.get("notes"),
    }


def _upsert(client, rows: list[dict], batch: int) -> int:
    inserted = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        client.table("inspiration_pages").upsert(chunk, on_conflict="id").execute()
        inserted += len(chunk)
        print(f"  [upsert] {inserted}/{len(rows)}")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE))
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate + summarize, no Supabase writes")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any file fails validation")
    parser.add_argument("--batch", type=int, default=100)
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.exists():
        print(f"[error] {source} not found", file=sys.stderr)
        return 1

    files = sorted(source.glob("*/*.json"))
    print(f"[scan] {len(files)} JSON files under {source}")

    mod = _load_validator()
    ok_rows: list[dict] = []
    failures: dict[str, list[str]] = {}
    seen_ids: dict[str, str] = {}

    for fp in files:
        issues = _validate_one(mod, fp)
        if issues:
            failures[str(fp.relative_to(REPO_ROOT))] = issues
            continue
        with fp.open(encoding="utf-8") as fh:
            d = json.load(fh)
        pid = d.get("id")
        if not pid:
            failures[str(fp.relative_to(REPO_ROOT))] = ["missing id"]
            continue
        if pid in seen_ids:
            failures[str(fp.relative_to(REPO_ROOT))] = [f"duplicate id {pid} (also in {seen_ids[pid]})"]
            continue
        seen_ids[pid] = str(fp.relative_to(REPO_ROOT))
        ok_rows.append(_to_row(d))

    print(f"[validate] {len(ok_rows)} ok, {len(failures)} fail")
    if failures:
        print(f"[skip] first 10 failing files:")
        for fp, issues in list(failures.items())[:10]:
            print(f"  - {fp}")
            for iss in issues[:3]:
                print(f"      · {iss}")
        if args.strict:
            return 2

    by_type: dict[str, int] = {}
    for r in ok_rows:
        by_type[r["page_type"]] = by_type.get(r["page_type"], 0) + 1
    print(f"[breakdown] {dict(sorted(by_type.items()))}")

    if args.dry_run:
        print("[dry-run] no writes performed")
        return 0

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

    n = _upsert(client, ok_rows, batch=args.batch)
    print(f"[done] upserted {n} rows into inspiration_pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
