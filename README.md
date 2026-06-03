# designlib-mcp

**Design knowledge for AI coding agents — curated, not hallucinated.**

A hand-curated catalog of design tokens, references, and patterns served over MCP. Drop-in source of truth for any AI coding agent.

→ [Quickstart](#quickstart) · [What sets it apart](#what-sets-it-apart) · [Tools](#tools)

**Live server:** `https://mcp.petbrains.dev/mcp`  
**Catalog:** 67 styles · 100 palettes · 34 font pairs · 134 domains · 25 chart types · 34 landing patterns · 105 icons · 405 inspiration pages · 120 animations · web + iOS  
**Status:** v1, production, read-only.

---

## The problem we keep hitting

When you ask an AI agent to "design a landing page for a fintech dashboard," it will happily invent `#2B7FFF`, pair Inter with Playfair, and move on. The tokens are plausible. They are also made up. Five prompts later the design has drifted, nothing matches, and you are hand-fixing colors that were never rooted in anything.

`designlib-mcp` replaces the guessing with a retrieval step.

---

## What sets it apart

**Hand-curated, not scraped or auto-generated.** Palettes, font pairs, styles, and references are authored — not pulled from low-quality sources or synthesized by a model. Every entry has a reason it is there.

**Role-mapped, not raw.** Palettes ship with `primary`, `surface`, `text_primary`, and contrast pairs already mapped — not just five hexes. Font pairs include weights, fallbacks, and `style_fit` tags. Icons come with ready-to-paste import code. Each catalog family is *agent-ready* — not raw data the agent has to interpret.

**MCP-native, client-agnostic.** Standard Model Context Protocol. Works in Claude Code, Claude Desktop, and any MCP-aware client. Not coupled to one tool.

**Read-only, no telemetry, hosted.** It does not write to your repo, does not call OpenAI, does not ship telemetry. Zero infra, zero secrets on your machine. It answers MCP queries and that is it.

---

## Quickstart

Point your MCP client at the hosted server.

### Claude Code

```bash
claude mcp add --transport http designlib https://mcp.petbrains.dev/mcp
claude mcp list
```

Then ask your agent:

```
Use designlib to find a palette and font pair for a fintech dashboard.
```

### Claude Desktop

Claude Desktop does not speak streamable-http natively — bridge it with [`mcp-remote`](https://www.npmjs.com/package/mcp-remote). Edit `claude_desktop_config.json`:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "designlib": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.petbrains.dev/mcp"]
    }
  }
}
```

Restart Claude Desktop. The `designlib` tools will appear.

### Other MCP-aware clients

Add an HTTP MCP server entry pointing at `https://mcp.petbrains.dev/mcp`.

---

## When to use it

Use it when:

- You are **building UI with an AI agent** and want consistent, non-hallucinated tokens across a session.
- You are **prototyping multiple styles** for the same product and want to compare them without re-authoring palettes each time.
- You are **scaffolding a design system** and need a sensible starting point keyed to a product domain.
- You are **generating marketing pages, dashboards, mobile screens** and want the agent to pick a coherent palette + typography combo instead of freestyling.

Skip it when:

- You already have a mature design system — use your own tokens.
- You need editable / writable storage — this server is read-only.
- You need brand-specific assets (logos, illustrations, custom icons). This catalog is about **tokens and style direction**, not brand identity.

---

## Tools

All 27 tools are read-only and platform-aware where applicable. Every `list_*` supports `limit` / `offset`; every `get_*` returns a `NOT_FOUND` payload when the id does not exist.

| Tool | Purpose | Key args |
|---|---|---|
| `list_styles` · `get_style` · `list_style_facets` | Complete design styles (palette + typography + density) | `platform`, `family`, `tone`, `density`, `tags` |
| `list_palettes` · `get_palette` · `list_palette_facets` | Palettes with role mapping and contrast pairs | `platform`, `family`, `mood`, `appearance` |
| `list_font_pairs` · `get_font_pair` · `list_font_pair_facets` | Heading + body + mono font pairings | `platform`, `category_id`, `style_fit` |
| `list_domains` · `get_domain` · `list_domain_facets` | Product domains with top-N style/palette/font recommendations | `category_id`, `audience`, `tone`, `top_n` |
| `list_chart_types` · `get_chart_type` · `list_chart_type_facets` | Chart types with when-to-use, accessibility grades, library picks | `data_type`, `a11y_grade`, `library`, `keyword` |
| `list_landing_patterns` · `get_landing_pattern` · `list_landing_pattern_facets` | Landing page layouts with section order and CTA placement | `keyword`, `cta_placement` |
| `list_icons` · `get_icon` · `list_icon_facets` | Individual icons with import code and usage snippets | `category`, `library`, `style`, `keyword` |
| `list_inspiration_pages` · `get_inspiration_page` · `list_inspiration_page_facets` | Curated real-world page references | `page_type`, `style_family`, `industry`, `mood`, `keyword` |
| `list_animations` · `get_animation` · `list_animation_facets` | Animation snippets with library, category, complexity | `category`, `framework`, `complexity`, `library`, `keyword` |

---

## Self-hosting

`designlib-mcp` is a stateless FastMCP server backed by a single **Postgres** database — no Supabase, no cloud lock-in. The only required secret is `DATABASE_URL`.

```bash
pip install -e .

export DATABASE_URL="postgresql://user:pass@host:5432/designlib"
export DESIGNLIB_TRANSPORT=http        # or pass --http
export PORT=8000

designlib-mcp                          # serves /mcp on $PORT
```

Or with Docker (the repo ships a `Dockerfile`):

```bash
docker build -t designlib-mcp .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host:5432/designlib" designlib-mcp
```

Bring up the schema with `migrations/selfhosted_schema.sql`, then load catalog data. The full operator guide — schema, seeding, and a Coolify + Hetzner deployment walkthrough — lives in **[docs/self-hosting.md](docs/self-hosting.md)**.

> The hosted `mcp.petbrains.dev` deployment runs this exact image against Postgres 16 behind [Coolify](https://coolify.io).

---

## Part of Pet Brains

`designlib-mcp` is one of three open-source tools we ship for builders who code with AI:

- **[mvp-builder](https://github.com/petbrains/mvp-builder)** — Document-Driven Development for Claude Code. Specs before code, TDD enforced, self-review catches stubs.
- **[design-builder](https://github.com/petbrains/design-builder)** — production-grade UIs from Claude Code without the AI-slop look. Uses `designlib-mcp` under the hood.
- **designlib-mcp** — this repo. The design-knowledge MCP. Standalone and client-agnostic.

Methodology and build films at [petbrains.dev](https://petbrains.dev) · YouTube [@petbrains](https://youtube.com/@petbrains)

---

## License

MIT. See [LICENSE](LICENSE).