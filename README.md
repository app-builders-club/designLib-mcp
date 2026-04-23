# designlib-mcp

> **A curated design-knowledge catalog for AI coding agents.**
> Stop letting Claude / Cursor / Copilot guess hex codes and font pairings. Give them a real, opinionated source of truth — over MCP.

**Live server:** `https://designlib-production.up.railway.app/mcp`
**Catalog:** 67 styles · 100 palettes · 34 font pairs · 134 domains · web + iOS
**Status:** v1, production, read-only.

---

## Why this exists

When you ask an LLM to "design a landing page for a fintech dashboard," it will happily invent `#2B7FFF`, pair Inter with Playfair, and move on. The tokens are plausible. They are also made up. Five prompts later the design has drifted, nothing matches, and you are hand-fixing colors that were never rooted in anything.

**designlib-mcp** replaces that guessing with a retrieval step. It exposes a hand-curated catalog of design styles, palettes, typography and domain recommendations through the Model Context Protocol, so any MCP-aware client (Claude Code, Claude Desktop, Cursor, IDE plugins) can fetch authoritative tokens on demand:

- Palettes with explicit role mapping (`primary`, `surface`, `text_primary`, contrast pairs) — not just five hexes.
- Font pairs with weights, fallbacks, sources and `style_fit` tags.
- Styles that bundle palette + typography + spacing + density into a cohesive token set.
- Domains (e.g. *fintech_dashboard*, *fitness_app*) with pre-computed top-N recommendations per platform.

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
```

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

**Deploy to Railway:**

```bash
npm i -g @railway/cli
railway login
railway init                   # Empty Project
railway add                    # Empty Service — link when prompted
railway variables --set "SUPABASE_URL=https://your-project.supabase.co" \
                  --set "SUPABASE_ANON_KEY=sb_publishable_..."
railway up                     # builds Dockerfile, deploys
railway domain                 # generate *.up.railway.app URL
```

Railway injects `PORT`; the Dockerfile sets `DESIGNLIB_TRANSPORT=http`; the server binds `0.0.0.0:$PORT`. Secrets live only in Railway Variables.
