# designlib-mcp

> **A curated design-knowledge catalog for AI coding agents.**
> Stop letting Claude / Cursor / Copilot guess hex codes and font pairings. Give them a real, opinionated source of truth — over MCP.

**Live server:** `https://designlib-production.up.railway.app/mcp`
**Catalog:** 67 styles · 100 palettes · 34 font pairs · 134 domains · 25 chart types · 34 landing patterns · 105 icons · web + iOS
**Status:** v1, production, read-only.

---

## Why this exists

When you ask an LLM to "design a landing page for a fintech dashboard," it will happily invent `#2B7FFF`, pair Inter with Playfair, and move on. The tokens are plausible. They are also made up. Five prompts later the design has drifted, nothing matches, and you are hand-fixing colors that were never rooted in anything.

**designlib-mcp** replaces that guessing with a retrieval step. It exposes a hand-curated catalog of design styles, palettes, typography and domain recommendations through the Model Context Protocol, so any MCP-aware client (Claude Code, Claude Desktop, Cursor, IDE plugins) can fetch authoritative tokens on demand:

- Palettes with explicit role mapping (`primary`, `surface`, `text_primary`, contrast pairs) — not just five hexes.
- Font pairs with weights, fallbacks, sources and `style_fit` tags.
- Styles that bundle palette + typography + spacing + density into a cohesive token set.
- Domains (e.g. *fintech_dashboard*, *fitness_app*) with pre-computed top-N recommendations per platform.
- Chart types with when-to-use / when-NOT-to-use guidance, accessibility grades and library recommendations.
- Landing patterns with section order, CTA placement and conversion optimization notes.
- Icons keyed to library, category and style, with ready-to-paste import code and usage snippets.

The server is **read-only by design**. It does not write to your repo, does not call OpenAI, does not ship telemetry. It answers queries over stdio or HTTP and that's it.

## When to use it

Use it when:

- You are **building UI with an AI agent** and want consistent, non-hallucinated tokens across a session.
- You are **prototyping multiple styles** for the same product and want to compare them without re-authoring palettes each time.
- You are **scaffolding a design system** and need a sensible starting point keyed to a product domain.
- You are **generating marketing pages, dashboards, mobile screens** and want the agent to pick a coherent palette + typography combo instead of freestyling.

Skip it when:

- You already have a mature design system — use your own tokens.
- You need editable / writable storage — this server is read-only.
- You need brand-specific assets (logos, illustrations, icons). This catalog is about **tokens and style direction**, not brand identity.

---

## Install

### Hosted (recommended)

Zero infra, zero secrets on your machine. Point your MCP client at the hosted server.

**Claude Code:**

```bash
claude mcp add --transport http designlib https://designlib-production.up.railway.app/mcp
claude mcp list
```

**Cursor / Windsurf / other MCP-aware clients:** add an HTTP MCP server entry pointing at `https://designlib-production.up.railway.app/mcp`.

**Claude Desktop** does not speak streamable-http yet — self-host over stdio (below).

### Self-hosted

Run your own copy when you want to customize the catalog, keep data inside your infra, or serve Claude Desktop over stdio.

**1. Provision Supabase.** Free tier is fine. From Project Settings → API, capture `SUPABASE_URL` and `SUPABASE_ANON_KEY`. From Settings → Database, capture `DATABASE_URL` (used only by the migration script). Copy `.env.example` → `.env` and fill them in.

**2. Install:**

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows bash; POSIX: .venv/bin/activate
pip install -e ".[dev]"
```

**3. Migrate + seed:**

```bash
python scripts/apply_migrations.py
python scripts/ingest_web.py
python scripts/compute_ios_medians.py
python scripts/ingest_ios.py
python scripts/ingest_content_catalog.py   # charts + landing patterns + icons
```

> The content-catalog ingest writes to RLS-protected tables, so it needs `SUPABASE_SERVICE_ROLE_KEY` in `.env` (or a `DATABASE_URL` with admin privileges if you adapt the script). The server itself keeps reading through the public anon key.

**4. Run:**

```bash
# stdio — Claude Desktop and other local MCP clients
designlib-mcp

# streamable-http — Claude Code and hosted deployments
designlib-mcp --http --port 8000
# or via env:
DESIGNLIB_TRANSPORT=http PORT=8000 designlib-mcp
```

HTTP endpoint: `POST /mcp`.

**Claude Desktop config (stdio)** — `%APPDATA%\Claude\claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Tools

All 21 tools are read-only and platform-aware where applicable. Every `list_*` supports `limit` / `offset`; every `get_*` returns a `NOT_FOUND` payload when the id does not exist.

| Tool | Purpose | Key args |
|---|---|---|
| `list_styles` · `get_style` · `list_style_facets` | Complete design styles (palette + typography + density) | `platform`, `family`, `tone`, `density`, `tags` |
| `list_palettes` · `get_palette` · `list_palette_facets` | Palettes with role mapping and contrast pairs | `platform`, `family`, `mood`, `appearance` |
| `list_font_pairs` · `get_font_pair` · `list_font_pair_facets` | Heading + body + mono font pairings | `platform`, `category_id`, `style_fit` |
| `list_domains` · `get_domain` · `list_domain_facets` | Product domains with top-N style/palette/font recommendations | `category_id`, `audience`, `tone`, `top_n` |
| `list_chart_types` · `get_chart_type` · `list_chart_type_facets` | Chart types with when-to-use, accessibility grades, library picks | `data_type`, `a11y_grade`, `library`, `keyword` |
| `list_landing_patterns` · `get_landing_pattern` · `list_landing_pattern_facets` | Landing page layouts with section order and CTA placement | `keyword`, `cta_placement` |
| `list_icons` · `get_icon` · `list_icon_facets` | Individual icons with import code and usage snippets | `category`, `library`, `style`, `keyword` |