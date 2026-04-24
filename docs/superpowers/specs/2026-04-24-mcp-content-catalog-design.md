# MCP Content Catalog Migration — Design Spec

**Date:** 2026-04-24
**Status:** Approved, ready for implementation plan
**Source:** `mcp-migration/` staging folder (charts.csv, landing.csv, icons.csv)

## Goal

Migrate three CSV datasets into Supabase and expose them through the designlib MCP server as read-only catalogs. After migration, the `mcp-migration/` folder is deleted — MCP becomes the single source of truth for this content.

**Scope (C):** code + ingest + tests + folder deletion. Version bump in `pyproject.toml` stays under user control.

## Data

| CSV | Rows | Becomes table | Becomes tools |
|---|---|---|---|
| `charts.csv` | 25 | `chart_types` | `list_chart_types`, `get_chart_type`, `list_chart_type_facets` |
| `landing.csv` | 34 | `landing_patterns` | `list_landing_patterns`, `get_landing_pattern`, `list_landing_pattern_facets` |
| `icons.csv` | 104 | `icons` | `list_icons`, `get_icon`, `list_icon_facets` |

Total: **3 tables + 9 new MCP tools** (12 → 21).

## Key Decisions

- **IDs:** semantic slugs (`chart_line_trend`, `landing_hero_features_cta`, `icon_phosphor_list`). Rationale: extensibility — new rows get meaningful IDs without renumbering, duplicates surface at ingest time, cross-links read naturally.
- **Keyword search:** `TEXT[]` + GIN index on every `keywords` column. Rationale: matches existing pattern (`domains.tone`, `palettes.tags`), O(log n) on `@>`/`&&`, avoids FTS overhead inappropriate for short tag sets.
- **Keyword tool arg:** single optional `keyword: str | None` (not a list). Matches the README spec. Internally: `.contains("keywords", [normalized])` — exact tag match, case-folded.
- **Migration file:** single `005_content_catalog.sql` — one logical wave.
- **Cleanup:** `mcp-migration/` is deleted after e2e passes. Not ambiguous — it's labelled staging.

## Schema (migration `005_content_catalog.sql`)

```sql
CREATE TABLE chart_types (
  id                     TEXT PRIMARY KEY,
  data_type              TEXT NOT NULL,
  keywords               TEXT[] NOT NULL DEFAULT '{}',
  best_chart_type        TEXT NOT NULL,
  secondary_options      TEXT[] NOT NULL DEFAULT '{}',
  when_to_use            TEXT NOT NULL,
  when_not_to_use        TEXT NOT NULL,
  data_volume_threshold  TEXT,
  color_guidance         TEXT,
  a11y_grade             TEXT NOT NULL,
  a11y_notes             TEXT,
  a11y_fallback          TEXT,
  library_recommendation TEXT[] NOT NULL DEFAULT '{}',
  interactive_level      TEXT,
  sort_order             INTEGER NOT NULL DEFAULT 0,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT valid_a11y_grade CHECK (a11y_grade IN ('AAA','AA','A','B','C','D'))
);
CREATE INDEX idx_chart_types_keywords ON chart_types USING GIN(keywords);
CREATE INDEX idx_chart_types_library  ON chart_types USING GIN(library_recommendation);
CREATE INDEX idx_chart_types_a11y     ON chart_types(a11y_grade);

CREATE TABLE landing_patterns (
  id                      TEXT PRIMARY KEY,
  name                    TEXT NOT NULL,
  keywords                TEXT[] NOT NULL DEFAULT '{}',
  section_order           TEXT NOT NULL,
  primary_cta_placement   TEXT NOT NULL,
  color_strategy          TEXT,
  recommended_effects     TEXT,
  conversion_optimization TEXT,
  sort_order              INTEGER NOT NULL DEFAULT 0,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_landing_patterns_keywords ON landing_patterns USING GIN(keywords);
CREATE INDEX idx_landing_patterns_cta      ON landing_patterns(primary_cta_placement);

CREATE TABLE icons (
  id           TEXT PRIMARY KEY,
  category     TEXT NOT NULL,
  icon_name    TEXT NOT NULL,
  keywords     TEXT[] NOT NULL DEFAULT '{}',
  library_id   TEXT REFERENCES icon_libraries(id) ON DELETE SET NULL,
  library_name TEXT NOT NULL,
  import_code  TEXT NOT NULL,
  usage        TEXT NOT NULL,
  best_for     TEXT,
  style        TEXT,
  sort_order   INTEGER NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_icons_category ON icons(category);
CREATE INDEX idx_icons_keywords ON icons USING GIN(keywords);
CREATE INDEX idx_icons_library  ON icons(library_id) WHERE library_id IS NOT NULL;
CREATE INDEX idx_icons_style    ON icons(style);

ALTER TABLE chart_types       ENABLE ROW LEVEL SECURITY;
ALTER TABLE landing_patterns  ENABLE ROW LEVEL SECURITY;
ALTER TABLE icons             ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON chart_types      FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "public_read" ON landing_patterns FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "public_read" ON icons            FOR SELECT TO anon, authenticated USING (true);
```

**Notes:**
- `a11y_grade` CHECK covers observed CSV values (AA/AAA/A/B/C/D).
- `icons.library_id` is a soft FK to existing `icon_libraries` — ingest resolves case-insensitive by name; unresolved rows keep FK NULL and still record `library_name` raw.
- `sort_order` preserves CSV `No` column for stable ordering.

## Pydantic Models (`src/designlib_mcp/models/`)

Three new files — `chart_type.py`, `landing_pattern.py`, `icon.py`. Each exposes `Summary` (for list items), full entity, and `Facets`. All use `ConfigDict(extra="forbid")`.

`a11y_grade` is `Literal["AAA","AA","A","B","C","D"]` on the full `ChartType` model.

Exports added to `models/__init__.py`.

## Repository (`src/designlib_mcp/repository/`)

Abstract methods added to `base.py`; concrete implementation in `supabase_repo.py`.

```python
def list_chart_types(*, data_type=None, a11y_grade=None, library=None,
                     keyword=None, limit=50, offset=0) -> dict
def get_chart_type(chart_id: str) -> dict | None
def list_chart_type_facets() -> dict

def list_landing_patterns(*, keyword=None, cta_placement=None,
                          limit=50, offset=0) -> dict
def get_landing_pattern(pattern_id: str) -> dict | None
def list_landing_pattern_facets() -> dict

def list_icons(*, category=None, library=None, style=None,
               keyword=None, limit=50, offset=0) -> dict
def get_icon(icon_id: str) -> dict | None
def list_icon_facets() -> dict
```

**Return shape:** `list_*` → `{"items": [...], "total": int, "limit": int, "offset": int}`. `facets` → lists of distinct values. `get_*` → full row dict or `None`.

**Keyword filter (uniform):**
```python
if keyword:
    normalized = keyword.strip().lower()
    query = query.contains("keywords", [normalized])
```

## MCP Tools (`src/designlib_mcp/tools/`)

Three new files: `chart_types.py`, `landing_patterns.py`, `icons.py`. Each follows the `palettes.py` pattern — standalone handler functions + `register(mcp, repo)`.

| Tool | Args |
|---|---|
| `list_chart_types` | `data_type?`, `a11y_grade?`, `library?`, `keyword?`, `limit`, `offset` |
| `get_chart_type` | `chart_id` |
| `list_chart_type_facets` | — |
| `list_landing_patterns` | `keyword?`, `cta_placement?`, `limit`, `offset` |
| `get_landing_pattern` | `pattern_id` |
| `list_landing_pattern_facets` | — |
| `list_icons` | `category?`, `library?`, `style?`, `keyword?`, `limit`, `offset` |
| `get_icon` | `icon_id` |
| `list_icon_facets` | — |

All tools: `readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true`. All responses pass through `enforce_character_limit`. `get_*` returns standard error shape `{error_code: "NOT_FOUND", message, field, suggest_tool}` when id not found.

Registration added to `server.py`.

## Ingest Script (`scripts/ingest_content_catalog.py`)

One script for all three CSVs, following `ingest_web.py`.

**Slug generation (deterministic):**
```python
def slugify(*parts: str) -> str:
    joined = "_".join(parts).lower()
    slug = re.sub(r"[^a-z0-9]+", "_", joined).strip("_")
    return re.sub(r"_+", "_", slug)

chart_id   = f"chart_{slugify(row['Best Chart Type'].split()[0], row['Data Type'])}"
landing_id = f"landing_{slugify(row['Pattern Name'])}"
icon_id    = f"icon_{slugify(row['Library'], row['Icon Name'])}"
```

**Keyword parsing:**
```python
def parse_keywords(raw: str) -> list[str]:
    tokens = re.split(r"[,\s]+", raw or "")
    seen, out = set(), []
    for t in tokens:
        t = t.strip().lower()
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out
```

**Other parsing:**
- `secondary_options`, `library_recommendation`: split on comma, trim, drop empties.
- `library_id` for icons: case-insensitive `SELECT id FROM icon_libraries WHERE LOWER(name) = LOWER(:library_name)` — attach if found, else NULL.
- `sort_order`: CSV `No` as integer.

**Slug collisions:** log warning; suffix with `_2`, `_3` etc. Unlikely at this scale but keeps future additions safe.

**Upsert:** `supabase.table(...).upsert(rows, on_conflict="id").execute()` — re-runnable without duplicates.

**Flags:** `--dry-run` prints what would be written, no DB writes.

## Tests

**Unit (~24 new tests):**
- `tests/models/test_chart_type.py`, `test_landing_pattern.py`, `test_icon.py` — schema validation, `extra="forbid"`, Literal enum checks (~3 tests each).
- `tests/repository/test_content_catalog.py` — query builder mocks: filters, `.contains` for keyword, limit/offset, facets distinct (~9 tests).
- `tests/tools/test_chart_types.py`, `test_landing_patterns.py`, `test_icons.py` — handlers: meta fields, NOT_FOUND error shape, `enforce_character_limit` invocation (~6 tests).
- `tests/scripts/test_ingest_content_catalog.py` — keyword parsing, slug generation, collision handling, library_id lookup (~6 tests).

**E2E (3 new tests, `integration` marker):**
- `tests/e2e/test_content_catalog_e2e.py` — one test per entity: `list → get → facets` through in-memory FastMCP Client against live Supabase.

**Final count:** 98 → ~125 tests (87+24 unit, 11+3 e2e).

## Implementation Order

1. Migration SQL + apply via `apply_migrations.py`
2. Pydantic models (TDD: tests → code)
3. Repository methods (TDD: tests → code)
4. MCP tools (TDD: tests → code)
5. Ingest script (TDD: tests → code)
6. Run ingest against Supabase
7. E2E tests (`integration` marker)
8. Update `README.md` — new tools in the tool reference table
9. Delete `mcp-migration/` + commit

## Out of Scope

- `pyproject.toml` version bump — user decides when to release.
- Pushing `main` to origin.
- Downstream skill plugin version bump (lives in a separate repo).
- In-process LRU cache for the new tools (can be added later, matches existing deferred decision on facets/recommendations).
