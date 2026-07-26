# Data model

`designlib-mcp` serves ten entity families. The access pattern is the same for every family: call `list_<entity>_facets` to discover valid filter values, call `list_<entity>(...)` with filters to get summaries, then call `get_<entity>(id)` for the full row. Every response is read-only, JSON, and capped at 25,000 characters; oversize responses set `meta.truncated = true` so the client knows to refine filters or lower `limit`.

→ Quickstart and tool index live in the [README](../README.md). This document describes what each family is *for*.

---

## styles

A **style** is a complete, named token set: palette + typography + layout + input + media + motion tokens, grouped under a style family (e.g. `editorial_serif`, `tactile_neo`, `data_dense_terminal`). Filter by `family`, `tone`, `density`, `appearance`, or `tags`. Tools: `list_styles`, `get_style`, `list_style_facets`. `get_style` returns full tokens plus `cross_links` to compatible palettes, font pairs, and domains. Reach for styles when the agent needs an end-to-end starting point — palette, type, motion, density — for a fresh UI rather than picking each layer independently. **Platform-aware:** `web` and `ios` are first-class; `platform` is required on every call.

## palettes

A **palette** is a role-mapped color set: `primary`, `surface`, `text_primary`, `text_secondary`, etc., plus pre-computed WCAG contrast pairs and a mood/strategy descriptor. Filter by `family`, `mood`, `appearance`, or `tags`. Tools: `list_palettes`, `get_palette`, `list_palette_facets`. Reach for palettes when the agent has a design direction in mind (e.g. "warm, editorial") and needs a coherent color foundation that already maps to UI roles instead of five raw hexes. **Platform-aware.**

## font_pairs

A **font pair** is a heading + body (and optional mono) combination with weights, fallbacks, Google Fonts URL, and `style_fit` tags. Filter by `category_id`, `style_fit`, or `tags`. Tools: `list_font_pairs`, `get_font_pair`, `list_font_pair_facets`. Reach for font pairs when a palette and density are already chosen and the agent needs typography that fits the same mood — without rolling its own pairing rules. **Platform-aware:** iOS pairs are anchored on SF Pro; web pairs span Google Fonts.

## domains

A **domain** is a product domain (e.g. `fintech_dashboard`, `developer_tools`, `wellness_app`) carrying its own metadata plus top-N `recommendations`: which styles, palettes, and font pairs are pre-scored as good fits. Filter by `category_id`, `audience`, or `tone` on `list_domains`. Tools: `list_domains`, `get_domain`, `list_domain_facets`. `get_domain(domain_id, platform, top_n=5)` returns the platform-filtered recommendation set. Reach for domains when the agent knows *what* it is building before it has decided *how* it should look — the catalog hands back curated style/palette/font candidates keyed to the domain. **Platform-agnostic for listing**, platform-aware for `get_domain` (recommendations are filtered to the requested platform; iOS recommendations are not yet populated in v1).

## chart_types

A **chart type** is a chart recipe with `data_type`, `best_chart_type`, secondary options, when-to-use / when-not-to-use prose, accessibility grade (`AAA`–`D`), and library recommendations. Filter by `data_type`, `a11y_grade`, `library`, or `keyword`. Tools: `list_chart_types`, `get_chart_type`, `list_chart_type_facets`. Reach for chart types when the agent needs to visualize data and wants a vetted answer — including accessibility grade — instead of defaulting to a generic bar chart.

## landing_patterns

A **landing pattern** is a section-order recipe for marketing landing pages: ordered section names, primary CTA placement, color and effect strategy, conversion guidance. Filter by `keyword` or `cta_placement`. Tools: `list_landing_patterns`, `get_landing_pattern`, `list_landing_pattern_facets`. Reach for landing patterns when scaffolding a marketing page — the pattern dictates the structural skeleton (hero → social proof → features → CTA …) before any styling is applied. Used as a soft reference from `inspiration_pages.landing_pattern_id`.

## icons

An **icon** is a single named glyph from a supported library (Phosphor, Lucide, Heroicons, etc.) with import code, usage snippet, category, and style tags. Filter by `category`, `library`, `style`, or `keyword`. Tools: `list_icons`, `get_icon`, `list_icon_facets`. Reach for icons when the agent needs ready-to-paste import code rather than guessing the right name and forgetting the import path.

## inspiration_pages

An **inspiration page** is one analyzed real-world reference: page type, ordered sections, palette, typography, primary CTA, mood, audience, and (for landings/signups) a generation prompt with hard/soft constraints. Filter by `page_type`, `appearance`, `style_family`, `industry`, `density`, `mood`, `keyword`, `signature`, `good_for_product_type`, or `good_for_stage`. Tools: `list_inspiration_pages`, `get_inspiration_page`, `list_inspiration_page_facets`. Reach for inspiration pages when the agent is about to *generate* a page and would benefit from a concrete reference — "what does a moody dark fintech landing look like?" — over abstract style tokens. → See [schemas/inspiration-pages.md](schemas/inspiration-pages.md) for the full row shape.

## animations

An **animation** is a UI animation snippet (background, hero, loader, text effect, cursor effect, decoration, etc.) with framework, libraries, complexity, interactivity, style tags, suggested placements, and a paste-ready prompt. Filter by `category`, `framework`, `interactivity`, `complexity`, `style_tag`, `placement`, `use_when`, `library`, or `keyword`. Tools: `list_animations`, `get_animation`, `list_animation_facets`. Reach for animations when the agent wants to add motion to a page and would otherwise hand-roll it — `get_animation` returns a standardized prompt that drops into the user's project.

## social_templates

A **social template** is a fillable design template for a story or carousel post: a self-contained HTML/CSS document (fixed 1080-px canvas per slide, `{{slot}}` placeholders, `:root` design tokens for re-skinning) plus the spec an LLM needs to fill it — per-slide slots with `max_chars`, a `content_brief` with tone and hook guidance, and slide roles (hook / content / proof / recap / cta). Repeatable slides make carousels variable-length; the `slides` filter matches templates whose min–max range covers the requested count. Filter by `format` (story | carousel), `category`, `aspect_ratio`, `appearance`, `platform` (social network: instagram | tiktok | linkedin | facebook), `style_tag`, `use_when`, `industry`, `keyword`, or `slides`. Tools: `list_social_templates`, `get_social_template`, `list_social_template_facets`. Summaries never carry the HTML (`html_chars` reports its size); `get_social_template(id, include_html=false)` returns the spec alone for cheap browsing. Reach for social templates when the task is "make me a carousel/story about X" — pick a template by purpose and format, fill its slots within their `max_chars`, then render or adapt the HTML. → See [schemas/social-templates.md](schemas/social-templates.md) for the full row shape and filling contract.

---

## Discovering filter values

Every entity ships a `list_<entity>_facets` tool that returns the *actually-populated* values for every filterable field — not the full schema vocabulary, just what the catalog currently contains. This is the recommended first call in any session: read the facets, then constrain the subsequent `list_<entity>(...)` query to values you saw in the facets response. The MCP returns structured `NOT_FOUND` errors with `suggest_tool` pointing at the correct `list_*` tool when an id is unknown, but it will *not* validate filter values against facets — passing an unknown filter simply returns an empty result set.

The character cap (`meta.truncated = true`) is your signal to either lower `limit` (default 25–50 depending on entity) or tighten filters. Pagination via `limit` + `offset` is supported on every `list_*` tool.
