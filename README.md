# designlib-mcp

A Python MCP server that exposes a curated design-knowledge catalog (web + iOS) over 12 read-only tools, backed by Supabase. Intended consumer: an external IDE/editor plugin that analyzes a project locally and pulls matching styles/palettes/font_pairs/domain data from this server.

## Quick start

### 1. Provision Supabase

Create a Supabase project (free tier is enough). Capture:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (from Project Settings → API — or the new "publishable" key format `sb_publishable_...`)
- `DATABASE_URL` (from Project Settings → Database → Connection string, "URI" format)

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

Note: `ingest_web.py` and `ingest_ios.py` write through the Supabase REST API. If your `SUPABASE_ANON_KEY` is scoped to read-only via RLS (the default after migration 001), switch to a service-role key for the ingest step, or drop RLS on the catalog tables if you don't need it.

### 4. Run

```bash
designlib-mcp
# or
python -m designlib_mcp
```

The server speaks MCP over stdio.

### 5. Wire into Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`
(or on Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

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

Restart Claude Desktop. The 12 tools appear under the `designlib` server.

## Tools

| Entity      | Tools                                                              |
| ----------- | ------------------------------------------------------------------ |
| Styles      | `list_styles`, `get_style`, `list_style_facets`                    |
| Palettes    | `list_palettes`, `get_palette`, `list_palette_facets`              |
| Font pairs  | `list_font_pairs`, `get_font_pair`, `list_font_pair_facets`        |
| Domains     | `list_domains`, `get_domain`, `list_domain_facets`                 |

## Plugin flow

A typical pull from the consumer plugin:

```
1. list_style_facets(platform="web")
       → discover available families, tones, densities
2. list_styles(platform="web", family="editorial", tone="literary")
       → shortlist with summaries
3. get_style(style_id="academia_classical")
       → full tokens + cross_links (compatible palettes/fonts/domains)
```

The server never receives project context — the plugin is authoritative about matching;
the server is a catalog.

## Source-only directories

`dump/`, `extraction/`, and `researches/` are NOT shipped with the repo; they are local
working folders used by the maintainer to seed Supabase (see `.gitignore`). End users who
just want to run the server don't need them — they only need a populated Supabase.

## Development

```bash
pytest -m "not integration"         # unit tests (no Supabase required)
pytest -m integration               # integration tests against live Supabase
ruff check src tests
```

See `docs/superpowers/specs/2026-04-22-designlib-mcp-v1-design.md` for the design spec
and `docs/superpowers/plans/2026-04-22-designlib-mcp-v1.md` for the implementation plan.
