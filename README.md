# designlib-mcp

A Python MCP server that exposes a curated design-knowledge catalog (web + iOS) over 12 read-only tools, backed by Supabase. Intended to be consumed by LLM-powered dev tools (Claude Code, Claude Desktop, IDE plugins) when they need authoritative, opinionated design tokens for a style — without hallucinating hex codes or font pairings.

- **67 styles**, **100 palettes**, **34 font pairs**, **134 domains** (web + iOS, mixed).
- **12 tools**: `list_*` / `get_*` / `list_*_facets` across 4 entities (styles, palettes, font_pairs, domains).
- **Two transports**: stdio (local, for Claude Desktop) and streamable-http (hosted, for Claude Code / remote clients).
- **Read-only**. The server never mutates state.

---

## Quick start

### 1. Provision Supabase

Free tier is enough. From Project Settings → API, capture:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (or the new `sb_publishable_…` format)
- `DATABASE_URL` from Settings → Database (used only by migrations)

Copy `.env.example` to `.env` and fill in those values.

### 2. Install

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows bash; POSIX: .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Apply migrations + seed

```bash
python scripts/apply_migrations.py
python scripts/ingest_web.py
python scripts/compute_ios_medians.py
python scripts/ingest_ios.py
```

Note: `ingest_*.py` write via the Supabase REST API. If RLS blocks writes (default after migration 001), use a service-role key for the ingest step.

### 4. Run

```bash
# stdio — for Claude Desktop and other local MCP clients
designlib-mcp

# streamable-http — for Claude Code and hosted deployments
designlib-mcp --http --port 8000
# or via env:
DESIGNLIB_TRANSPORT=http PORT=8000 designlib-mcp
```

HTTP endpoint: `POST /mcp`.

---

## Wire into a client

### Claude Code (HTTP, recommended once hosted)

```bash
claude mcp add --transport http designlib https://<your-host>/mcp
claude mcp list
```

Zero client-side config — the hosted server holds Supabase credentials.

### Claude Desktop (stdio)

`~/Library/Application Support/Claude/claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "designlib": {
      "command": "designlib-mcp",
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_ANON_KEY": "sb_publishable_..."
      }
    }
  }
}
```

---

## Deploy to Railway

```bash
npm i -g @railway/cli
railway login
railway init                   # Empty Project
railway add                    # Empty Service — link it when prompted
railway variables --set "SUPABASE_URL=https://your-project.supabase.co" \
                  --set "SUPABASE_ANON_KEY=sb_publishable_..."
railway up                     # builds Dockerfile, deploys
railway domain                 # generate *.up.railway.app URL
```

Railway injects `PORT`; the Dockerfile sets `DESIGNLIB_TRANSPORT=http`; the server binds `0.0.0.0:$PORT`. Secrets live only in Railway Variables — never in the client config or on disk.

---

## Usage

### Tool reference

All tools return `{ ..., meta: { schema_version, platform, entity_type, truncated } }`. Lists also return `{ items, total_count, limit, offset, meta }`. Unknown-id responses return `{ error_code: "NOT_FOUND", message, field, suggest_tool }` instead of an exception.

| Tool | Arguments | Purpose |
|---|---|---|
| `list_style_facets` | `platform: "web" \| "ios"` | Available families, tones, densities, appearances, tag_vocabulary |
| `list_styles` | `platform`, `family?`, `appearance?`, `tone?`, `density?`, `tags?: string[]`, `limit=50`, `offset=0` | Shortlist of styles with summaries |
| `get_style` | `style_id: string`, `include_cross_links=true`, `cross_links_limit=5` | Full tokens + cross-links to palettes / font_pairs / domains |
| `list_palette_facets` | `platform` | Available families, moods, appearances, tag_vocabulary |
| `list_palettes` | `platform`, `family?`, `appearance?`, `mood?`, `tags?: string[]`, `limit=50`, `offset=0` | Shortlist of palettes |
| `get_palette` | `palette_id: string` | Full role mapping (primary/surface/text/etc.), contrast pairs |
| `list_font_pair_facets` | `platform` | Available categories, style_fit vocabulary, tag_vocabulary |
| `list_font_pairs` | `platform`, `category_id?`, `style_fit?: string[]`, `tags?: string[]`, `limit=50`, `offset=0` | Shortlist of font pairs |
| `get_font_pair` | `font_pair_id: string` | Heading / body / mono specs with weights, sources, fallbacks |
| `list_domain_facets` | — | Available categories, audiences, tones |
| `list_domains` | `category_id?`, `audience?`, `tone?`, `limit=50`, `offset=0` | Platform-agnostic domain catalog |
| `get_domain` | `domain_id: string`, `platform: "web" \| "ios"`, `top_n=5` | Domain with top-N style / palette / font recommendations for the requested platform |

### Typical workflow

A client plugin (or an LLM agent) consulting the catalog for a fintech dashboard would typically:

```
1. list_domain_facets()
       → learn categories / audiences / tones
2. list_domains(audience="fintech", tone="trustworthy")
       → shortlist of relevant domains
3. get_domain(domain_id="fintech_dashboard", platform="web", top_n=3)
       → top 3 styles + their palettes + font pairs for web
4. get_style(style_id="...") / get_palette(palette_id="...")
       → full tokens for the chosen style/palette
```

Or, for a style-first flow:

```
1. list_style_facets(platform="ios")
       → 10 iOS families with their tones/densities
2. list_styles(platform="ios", family="fitness_vitality", limit=5)
3. get_style(style_id="fitness_vitality_ios")
       → tokens + cross_links.palettes/font_pairs/domains
```

### Prompting tips

When asking an LLM with this MCP wired in:

- **"Find me a design style for a fintech dashboard and give me the palette + typography"** → the model will naturally chain `list_domains` → `get_domain` → `get_palette` → `get_font_pair`.
- **"Show me all iOS-native styles"** → `list_styles(platform="ios")`.
- **"What are the tokens for academia_classical?"** → `get_style(style_id="academia_classical")`.
- Ask the model to **call `list_*_facets` first** when it doesn't know what values are valid for `family` / `tone` / `audience`. Tools are self-documenting but the model sometimes invents values without checking.

### Response envelope

```json
{
  "items": [ { "id": "...", "name": "...", "summary": "...", ... } ],
  "total_count": 57,
  "limit": 50,
  "offset": 0,
  "meta": {
    "schema_version": "1.0",
    "platform": "web",
    "entity_type": "style_list",
    "truncated": false
  }
}
```

Payloads that would exceed 25 000 characters are truncated with `meta.truncated=true`. In practice this only trips on very wide `list_*` calls — lower `limit` or paginate.

---

## Architecture

- `src/designlib_mcp/server.py` — FastMCP app, registers the 12 tools
- `src/designlib_mcp/tools/` — one module per entity (styles / palettes / font_pairs / domains)
- `src/designlib_mcp/repository/` — `CatalogRepository` Protocol + Supabase implementation
- `src/designlib_mcp/services/cross_links.py` — style→palette/font/domain cross-linking via `recommendation_scores`
- `src/designlib_mcp/models/` — Pydantic v2 response models
- `migrations/` — 4 SQL files (base schema → platform column → iOS extensions → dna columns)
- `scripts/` — migrations runner, iOS median pipeline, web/iOS ingest
- `data/` — hand-authored iOS family definitions + computed medians (checked in for reproducibility)

### Source-only directories

`dump/`, `extraction/`, `researches/` are **NOT shipped with the repo**; they are local working folders the maintainer uses to seed Supabase. End users of the server just need a populated Supabase.

---

## Development

```bash
pytest -m "not integration"      # unit tests (no Supabase required) — 87 tests
pytest -m integration            # integration + e2e tests against live Supabase — 11 tests
pytest                           # everything
ruff check src tests
```

The e2e suite (`tests/e2e/`) spins up the real FastMCP server in-memory and calls every tool through the MCP protocol against a live Supabase, including roundtrips (`list_*` → pick ID → `get_*`) and error paths (NOT_FOUND).

See `docs/superpowers/specs/2026-04-22-designlib-mcp-v1-design.md` for the design spec and `docs/superpowers/plans/2026-04-22-designlib-mcp-v1.md` for the implementation plan.
