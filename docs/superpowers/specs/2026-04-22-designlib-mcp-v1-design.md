# designlib-mcp — v1 Design

**Status:** Draft (pending user approval)
**Date:** 2026-04-22
**Author:** Roman Pluzhnikov (via brainstorming session)

---

## 1. Goal and Scope

Python MCP server `designlib-mcp` that exposes a curated design-knowledge catalog (web + iOS) to a separate IDE/editor plugin. The plugin analyzes the user's project locally, then queries this MCP to **pull** matching style/palette/font/domain data. Read-only. No project context is sent into the server.

### In scope (v1)

Four entities:

1. **Styles** — full token sets (colors, typography, layout, inputs, media, motion) grouped by style-family.
2. **Palettes** — color palettes with role mapping, contrast pairs, mood tagging.
3. **Font pairs** — heading/body/mono combinations with fallbacks, google fonts urls, style/domain fit.
4. **Domains** — 134+ domains with attached recommendations (styles/palettes/fonts) for web.

Two platforms: `web` (curated DB from legacy Design Prompt Builder v2) and `ios` (normalized from vision-extracted app profiles). Symmetric API — `platform` is a required filter on every `list_*` tool.

### Access model

`list + get + facets + cross-links` (no semantic search, no project-context ranking):

1. Plugin calls `list_*_facets(platform)` once to learn available values for `family`, `tone`, `density`, `appearance`, etc.
2. Plugin calls `list_*(platform, filters, limit, offset)` to get a shortlist with summaries.
3. Plugin calls `get_*(id)` for full tokens, with optional `cross_links` showing compatible palettes/fonts/domains scored from `recommendation_scores` (web only in v1).

### Out of scope (v1 — may come in v2+)

Components/patterns/section references, app-reference browsing tool, animations, icons, backgrounds, cross-platform mapping, semantic search, project-context ranking, iOS recommendation_scores, PyPI release, CI.

### Non-goals / explicit exclusions

- MCP never receives project tokens, brand colors, or descriptions. The plugin is authoritative about matching; MCP is a catalog.
- No user-generated content. `profiles` and `projects` tables from the legacy DB are not migrated.

---

## 2. Stack and Architecture

**Language:** Python 3.11+. **Framework:** FastMCP + Pydantic v2. **Storage:** Supabase (Postgres). **Client lib:** `supabase-py`. **Transport:** stdio.

**Rationale for Supabase:** user chose it to allow catalog updates without MCP redeploy and to keep a migration path to pgvector for future semantic search. Accepted tradeoffs: network latency per tool call, single point of failure, service-key handling (acceptable — user runs MCP locally for themselves + plugin users in a controlled setup).

### Repository layout

```
designlib-mcp/
├── src/designlib_mcp/
│   ├── __init__.py
│   ├── server.py                # FastMCP app, registers all 12 tools
│   ├── config.py                # env vars, constants (CHARACTER_LIMIT = 25_000)
│   ├── models/                  # Pydantic v2 response models
│   │   ├── common.py            # Platform, Appearance, Density, ResponseMeta, PaginatedResponse, MCPError, FacetValue
│   │   ├── style.py             # ColorTokens, TypographyTokens, LayoutTokens, InputTokens, MediaTokens, MotionTokens, StyleTokens, IosMetadata, StyleSummary, Style, StyleCrossLinks, StyleFacets
│   │   ├── palette.py           # ColorRole, ContrastPair, PaletteSummary, Palette, PaletteFacets
│   │   ├── font_pair.py         # FontSpec, FontPairSummary, FontPair, FontPairFacets
│   │   └── domain.py            # DomainSummary, Domain, DomainRecommendations, DomainFacets
│   ├── repository/
│   │   ├── base.py              # CatalogRepository Protocol (abstract interface)
│   │   └── supabase_repo.py     # SupabaseRepository (v1 implementation)
│   ├── tools/                   # one module per entity, 3 tools each
│   │   ├── styles.py            # list_styles, get_style, list_style_facets
│   │   ├── palettes.py          # list_palettes, get_palette, list_palette_facets
│   │   ├── font_pairs.py        # list_font_pairs, get_font_pair, list_font_pair_facets
│   │   └── domains.py           # list_domains, get_domain, list_domain_facets
│   ├── services/
│   │   ├── cross_links.py       # style_id → top-N palettes/fonts/domains via recommendation_scores
│   │   └── normalizer.py        # DB row → Pydantic model
│   └── formatting/
│       └── truncate.py          # enforces CHARACTER_LIMIT with truncated flag
├── scripts/                     # one-shot ingest, run manually by maintainer
│   ├── compute_ios_medians.py   # extraction/aggregated/*.json → data/ios_family_medians.json
│   ├── ingest_web.py            # dump/db-dump/tables/*.json → Supabase
│   └── ingest_ios.py            # medians + definitions → Supabase
├── migrations/
│   ├── 001_base_schema.sql      # reused from dump/db-dump/supabase-source
│   ├── 002_platform_column.sql  # ALTER + ENUM + indexes
│   └── 003_ios_extensions.sql   # design_styles.ios_metadata JSONB + ios_app_profiles table
├── data/                        # versioned artifacts (committed)
│   ├── ios_family_medians.json          # generated by compute_ios_medians.py, checked in for reproducibility
│   └── ios_family_definitions.json      # hand-authored from researches/ — canonical iOS family descriptions
├── tests/
│   ├── conftest.py
│   ├── test_styles.py
│   ├── test_palettes.py
│   ├── test_font_pairs.py
│   ├── test_domains.py
│   └── fixtures/                # recorded Supabase responses for offline tests
├── pyproject.toml
├── README.md
├── .env.example
└── .gitignore
```

### Source-only directories (NOT committed, in `.gitignore`)

- `dump/` — legacy Design Prompt Builder v2 dump (source for `ingest_web.py`)
- `extraction/` — iOS vision-extraction pipeline output (source for `compute_ios_medians.py` and `ingest_ios.py`)
- `researches/` — deep-research markdown artifacts (source for hand-writing `data/ios_family_definitions.json`)

These are local working directories used by the maintainer to build `data/*.json` and seed Supabase. The repo ships as a clean library: MCP code + migrations + versioned `data/*.json` + tests. End users of the MCP (or the plugin) never touch these source folders.

### Architectural principles

- **Repository pattern.** Tools depend on `CatalogRepository` Protocol. Swapping Supabase for another backend later (or mocking in tests) requires no tool changes.
- **One module per entity.** Easy discovery, easy to add a fifth entity.
- **Cross-links as a separate service.** Not duplicated across tools.
- **No cache in v1.** Catalog is small (~3MB logical). Add `cachetools.TTLCache` later if measured to be a bottleneck.
- **Ingest scripts live outside the server.** MCP never writes to the DB.

---

## 3. Data Model

Starting point: existing web schema from `dump/db-dump/supabase-source/migrations/001_initial_schema.sql`.

### Migration 002 — platform column

```sql
CREATE TYPE platform AS ENUM ('web', 'ios');

ALTER TABLE style_families ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE design_styles  ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE color_palettes ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE font_pairs     ADD COLUMN platform platform NOT NULL DEFAULT 'web';
-- domains and recommendation_scores are platform-agnostic in v1.

CREATE INDEX idx_design_styles_platform ON design_styles(platform);
CREATE INDEX idx_color_palettes_platform ON color_palettes(platform);
CREATE INDEX idx_font_pairs_platform     ON font_pairs(platform);
```

### Migration 003 — iOS extensions

```sql
-- iOS-specific fields on design_styles
ALTER TABLE design_styles ADD COLUMN ios_metadata JSONB;
-- Shape (nullable for web, required for ios):
-- {
--   "liquid_glass_posture": "native_fit|selective|none|unclear",
--   "surfaces_affected": ["tab_bar","toolbar","modal_sheet",...],
--   "list_style_dominant": "inset_grouped|plain|card_grid|...",
--   "density_typical": "compact|comfortable|spacious",
--   "appearance_support": ["light","dark"] | ["light"] | ["dark"],
--   "corner_radius_cards_pt_median": 16,
--   "iconography": "sf_symbols_only|custom_glyph_set|mixed|photographic|unclear",
--   "reference_apps": ["linear","things_3","bear"]
-- }

-- Reference app profiles (populated in v1, no tools exposed; v2 will add browse tool)
CREATE TABLE ios_app_profiles (
  slug        TEXT PRIMARY KEY,
  family_id   TEXT REFERENCES style_families(id),
  aggregated  JSONB NOT NULL,  -- entire extraction/aggregated/{slug}.json
  screenshot_count INT,
  confidence  TEXT             -- high|medium|low from family_assignments.json
);
```

### iOS seed plan

- **style_families +10** (`platform='ios'`): `enterprise_muted`, `fitness_vitality`, `editorial_photography`, `minimalist_monochrome`, `data_dense_terminal`, `warm_handcrafted`, `editorial_canvas`, `tactile_depth_playful`, `youth_social_widget`, `system_default_plus`. Descriptions/keywords/anti_patterns authored by hand in `data/ios_family_definitions.json`.
- **design_styles +10** (`platform='ios'`, one per family in v1, id = `"{family}_ios"`). `tokens.colors` from median light palette. `tokens.typography` from majority classification. `ios_metadata` from medians.
- **color_palettes +10 to +20** (`platform='ios'`): one light palette per family (required) + dark where ≥3 apps in family have dark mode. `source = 'ios_aggregated'`, `reference_apps` populated.
- **font_pairs +6** (`platform='ios'`): canonical iOS combinations: `sf-pro-text + sf-pro-display`, `sf-pro-text + new-york-serif`, `sf-pro-rounded + sf-pro-rounded`, `sf-pro-text + custom-serif`, `sf-pro-text + custom-sans`, `sf-mono + sf-pro-display`.
- **ios_app_profiles +52** — raw aggregated JSON per app.
- **recommendation_scores** — web data only in v1 (365 rows). iOS scores deferred to v2.

---

## 4. Tools (12 total)

All tools: `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true`, `openWorldHint=true`. Responses in JSON (Pydantic `.model_dump()`). Serialized response is capped at `CHARACTER_LIMIT = 25_000` characters (not tokens); when exceeded, the paginated `items` list is truncated and the response is returned with `meta.truncated = true` and a hint to apply stricter filters or reduce `limit`.

### Styles

- **`list_styles(platform, family?, appearance?, tone?, density?, tags?, limit=50, offset=0)`** → `PaginatedResponse[StyleSummary]`
- **`get_style(style_id, include_cross_links=true, cross_links_limit=5)`** → `Style` (full tokens + cross_links)
- **`list_style_facets(platform)`** → `StyleFacets` (families, tones, densities, appearances, tag_vocabulary with counts)

### Palettes

- **`list_palettes(platform, family?, appearance?, mood?, tags?, limit=50, offset=0)`** → `PaginatedResponse[PaletteSummary]`
- **`get_palette(palette_id)`** → `Palette` (roles, contrast_pairs, mood, source, reference_apps, used_by_styles)
- **`list_palette_facets(platform)`** → `PaletteFacets` (families, moods, appearances, background_modes)

### Font pairs

- **`list_font_pairs(platform, category_id?, style_fit?, tags?, limit=50, offset=0)`** → `PaginatedResponse[FontPairSummary]`
- **`get_font_pair(font_pair_id)`** → `FontPair` (heading/body/mono FontSpec, fallbacks, google_fonts_url, style_fit, domain_fit, compatible_styles)
- **`list_font_pair_facets(platform)`** → `FontPairFacets` (categories, tags)

### Domains

- **`list_domains(category_id?, audience?, tone?, limit=50, offset=0)`** → `PaginatedResponse[DomainSummary]` (platform-agnostic, no platform filter)
- **`get_domain(domain_id, platform, top_n=5)`** → `Domain` with `recommendations: DomainRecommendations` (top-N styles/palettes/fonts filtered by platform; empty for iOS in v1)
- **`list_domain_facets()`** → `DomainFacets` (categories, audiences, tones, data_densities, ui_patterns)

### Conventions

- **Pagination:** `items`, `total_count`, `limit`, `offset` in every paginated response.
- **Meta envelope:** every response has `meta: { schema_version: "1.0", platform?, entity_type, truncated }`.
- **Error format:** `MCPError { error_code, message, field?, available_values?, suggest_tool? }` — messages are actionable, e.g. `"Unknown family 'foo'. Call list_style_facets to see available values."`

---

## 5. Response Models (Pydantic v2)

Full Pydantic class definitions will live in `src/designlib_mcp/models/*.py` and are authoritative there. Key invariants of the response shape:

- **`StyleTokens`** composes `ColorTokens` (17+ roles + `extras: dict[str, str]` escape hatch), `TypographyTokens`, `LayoutTokens`, `InputTokens`, `MediaTokens`, `MotionTokens`.
- **`IosMetadata`** is optional on `Style`, populated only for `platform == ios`.
- **`StyleCrossLinks`** has `palettes`, `font_pairs`, `domains` each with `id`, `name`, `score` (nullable for iOS v1), optional `reason`.
- **`Palette.contrast_pairs`** — pre-computed WCAG ratios (AA/AAA × normal/large) for critical role combos (text_primary × background, text_secondary × background, text_on_primary × primary, etc.). Computed once at ingest time.
- **`FontSpec.is_system_font=true`** for SF Pro family (no download URL).
- **`DomainRecommendations`** holds summaries (not full objects) to stay under character limit; plugin drills into full objects via `get_*` if needed.

---

## 6. iOS Normalization Pipeline (one-shot ingest)

Three scripts in `scripts/`, run manually in order.

### `compute_ios_medians.py`

**Input:** `extraction/aggregated/*.json` + `extraction/family_assignments.json`
**Output:** `data/ios_family_medians.json` (committed to repo for reproducibility)

Per iOS family:

1. Gather apps with `family_assigned == family` and `confidence != "low"`.
2. **Palette (light):** median of each role hex across apps in LAB color space. Drop apps with `background_conflicting=true` when computing background. Record top-3 candidate accents by frequency.
3. **Palette (dark):** same, only if ≥3 apps have dark coverage. Otherwise `appearance_support: ["light"]`.
4. **Typography:** majority vote on `body` and `heading` classification; `mono_present`/`tabular_numerics_present` OR-aggregated.
5. **Layout:** mode of `list_style_dominant`, mode of `density_typical`, median of `corner_radius_cards_pt_median`.
6. **Liquid glass:** mode of `posture`; union of `surfaces_affected` at ≥70% frequency.
7. **Iconography:** mode of `icon_system`.
8. **Reference apps:** top-5 by `screenshot_count × confidence_weight`, where `confidence_weight` is `high=1.0`, `medium=0.6` (rows with `confidence=low` were filtered out in step 1).

Record `review_flags` per family when: app_count < 3, >50% apps with `high_conflict_palette`, >50% with `typography_uncertain`.

### `ingest_web.py`

**Input:** `dump/db-dump/tables/*.json`

1. Apply migrations 001, 002, 003.
2. Upsert all catalog tables with `platform='web'`: `style_families`, `design_styles`, `color_palettes`, `font_pairs`, `font_pair_categories`, `color_psychology`, `domains`, `domain_categories`, `recommendation_scores`, `icon_libraries`, `ui_libraries`, `background_types`, `animation_presets`, `animation_themed_collections`, `app_config`.
3. Skip: `profiles` (empty), `projects` (user-generated), VIEW tables (recreated as VIEWS in migration).
4. Validate: row counts match `_summary.json`.

### `ingest_ios.py`

**Input:** `data/ios_family_medians.json` + `data/ios_family_definitions.json` + `extraction/aggregated/*.json` + `extraction/family_assignments.json`

1. Insert 10 `style_families` with `platform='ios'`.
2. Insert 10 `design_styles` (one per family, id = `"{family}_ios"`, tokens from medians, `ios_metadata` populated).
3. Insert 10–20 `color_palettes` (`source='ios_aggregated'`, `reference_apps` set).
4. Insert 6 canonical `font_pairs`.
5. Insert 52 `ios_app_profiles` rows (raw aggregated JSON as JSONB).

### Idempotency and reset

All ingests are `UPSERT` by primary key. Repeated runs are safe. Optional `scripts/reset_ios.py --confirm` deletes `WHERE platform='ios'` across catalog tables plus `TRUNCATE ios_app_profiles` for clean re-ingest.

### Manual work (not automated)

- `data/ios_family_definitions.json` — hand-authored from `researches/compass_artifact_*.md`. Provides each family's `description`, `emotional_keywords`, `anti_patterns`, `visual_signatures`. ~2 hours of editorial work. Without it, iOS styles are bland stubs.
- Post-ingest calibration: compare Supabase rows against the 5 hand-calibrated apps in `extraction/calibration/*.json`. If medians diverge significantly, tune parameters in `compute_ios_medians.py` and re-run.

### CLI

```bash
python scripts/compute_ios_medians.py          # writes data/ios_family_medians.json
python scripts/ingest_web.py --env .env.local  # web rows
python scripts/ingest_ios.py --env .env.local  # iOS rows
```

---

## 7. Release v1 — Acceptance Criteria

### Definition of Done

1. Supabase instance up; migrations 001/002/003 applied; `ingest_web.py` completes; row counts match `_summary.json`.
2. `data/ios_family_medians.json` generated; `review_flags` on < 30% of rows.
3. `ingest_ios.py` completes: 10 style_families, 10 design_styles, 10–20 palettes, 6 font_pairs, 52 ios_app_profiles inserted with `platform='ios'` where applicable.
4. `data/ios_family_definitions.json` authored.
5. All 12 tools have smoke tests that call via a FastMCP client and validate the Pydantic response model.
6. MCP launches locally (`uv run designlib-mcp` or `python -m designlib_mcp`), connects to Supabase via env, responds to `tools/list` and `tools/call`.
7. Integration verified with Claude Desktop: MCP registered, all 12 tools visible, `get_style("academia_classical")` returns full tokens in < 1s.
8. `README.md` covers install, env vars, and an example plugin flow (facets → list → get).

### Not blocking v1

- iOS `recommendation_scores` (plugin uses attribute filters instead).
- In-process cache (Supabase read path is fast enough for v1 scale).
- CI pipeline (tests run manually).
- PyPI release (install via `pip install -e .` from repo).

### Timeline estimate (single-developer calendar)

- Supabase setup + migrations: 0.5d
- `compute_ios_medians.py` + calibration: 1d
- `ingest_web.py` + `ingest_ios.py`: 0.5d
- `ios_family_definitions.json` (hand-authored): 0.5d
- 4 tool modules + Pydantic models + repository: 2d
- Smoke tests + Claude Desktop integration: 0.5d
- **Total: ~5 working days**

---

## 8. Open Questions / Deferred Decisions

- **Supabase hosting tier:** free tier sufficient for v1 maintainer-only use; re-evaluate if plugin is distributed broadly.
- **Authentication:** v1 uses `SUPABASE_ANON_KEY` + RLS read-only policies on catalog tables. If the plugin is distributed, decide between (a) shipping anon key in plugin package (safe with RLS) or (b) proxying through a backend. Not v1 scope.
- **v2 roadmap** — explicitly deferred until v1 ships and is used in the plugin.
