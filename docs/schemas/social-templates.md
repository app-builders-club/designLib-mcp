# social_templates — schema reference

One row = one fillable design template for a story or carousel post: metadata
for retrieval, a slides/slots spec for the filling LLM, and a self-contained
HTML/CSS document that renders the design. Collected and authored per
`mcp-migration/social-templates/PROTOCOL.md`; loaded via
`scripts/emit_social_templates_sql.py` output applied manually.

Table: `social_templates` (migration `009_social_templates.sql`).

## Row shape

### Identification

| column | type | notes |
|---|---|---|
| `id` | TEXT PK | `social_<format>_<descriptor>`, e.g. `social_carousel_pastel_listicle` |
| `title` | TEXT | Title Case pattern name |
| `source` | TEXT | `canva_gallery · adobe_express_gallery · dribbble · behance · original · other` — where the *pattern* was observed |
| `source_url` | TEXT? | provenance link (pattern inspiration only; markup and copy are original) |
| `source_note` | TEXT? | one-line provenance note |
| `preview_path` | TEXT? | local render path on the maintainer's machine; not a served asset |

### Classification (filterable scalars)

| column | values | notes |
|---|---|---|
| `format` | `story · carousel` | stories are single-view 9:16; carousels swipe |
| `aspect_ratio` | `9:16 · 4:5 · 1:1` | canvas px: 1080×1920 / 1080×1350 / 1080×1080; story ⇒ always 9:16 (CHECK) |
| `appearance` | `light · dark · mixed` | dominant scheme as authored (re-skinnable via tokens) |
| `category` | `promo · product_showcase · educational · listicle · checklist · quote · announcement · testimonial · personal_story · before_after · event · engagement` | content purpose |
| `slide_count` | INT | slides authored in `html_template` |
| `min_slides` / `max_slides` | INT | allowed range after removing/duplicating repeatable slides; fixed template ⇒ min = count = max |

### Tag arrays (GIN-filterable, lowercased at ingest)

| column | vocabulary | notes |
|---|---|---|
| `platform_fit` | closed: `instagram · tiktok · linkedin · facebook` | enforced by CHECK |
| `style_tags` | open, seeded in PROTOCOL.md §6 | visual DNA: `pastel`, `bold_type`, `editorial_serif`, … |
| `use_when` | open, seeded | situations: `sale_promotion`, `tips_series`, `social_proof`, … |
| `keywords` | free | search words |
| `industry_fit` | open, seeded | broad: `saas`, `creator`, `fitness`, … |

### Structured (JSONB)

**`slides`** — ordered array, one entry per authored slide:

```json
{
  "index": 2,
  "role": "content",                  // hook | content | proof | recap | cta
  "layout_note": "Numbered card: display-scale numeral, imperative title, two-line body.",
  "repeatable": true,                 // filler may duplicate/remove this slide
  "slots": [
    {"name": "point_title", "type": "headline", "max_chars": 40, "required": true,
     "hint": "One idea, imperative.", "example": "Lead with the outcome"}
  ]
}
```

Slot `type` vocabulary: `headline · subhead · body · bullet_list · cta · kicker ·
quote · stat · badge · handle · image_slot · avatar_slot · logo_slot`.
Slot names are unique across the whole template — they ARE the placeholder
tokens in the HTML.

**`fonts`** — `[{role, family, google_font, weights, fallback}]`, mirrors the
Google Fonts `<link>` in the HTML so a consuming app can preload or substitute.

### The HTML template

`html_template` is one self-contained HTML document:

- Slides are sibling `<section class="slide" data-slide="N" data-role="…">`
  elements with a fixed pixel canvas. Repeatable slides carry
  `data-repeat="true"`; optional elements carry `data-optional="true"`.
- Text slots appear as `{{slot_name}}` tokens; structural slots
  (`image_slot`, `bullet_list`, `avatar_slot`, `logo_slot`) as
  `data-slot="slot_name"` containers with neutral placeholder content.
- `:root` always defines the token contract:
  `--bg, --surface, --accent, --accent-contrast, --text-primary,
  --text-secondary, --font-display, --font-body` — override these 8 variables
  to re-skin the template to a brand without touching markup.
- No JavaScript, no base64, no external assets beyond Google Fonts.
  Ingest-capped at 20,000 chars.

### Prose

| column | shape |
|---|---|
| `description` | 2–4 sentences: what it is + dominant visual idea |
| `why_it_works` | 2–4 sentences: attention mechanics, swipe logic |
| `content_brief` | imperative guidance for the filling LLM: tone, hook formula, char discipline, CTA advice |

## Querying via MCP

### `list_social_templates` · `get_social_template`

Filters: `format`, `category`, `aspect_ratio`, `appearance`, `platform`
(social network, NOT the repo-wide web/ios axis), `style_tag`, `use_when`,
`industry`, `keyword`, `slides` (int: matches `min_slides <= N <= max_slides`),
`limit` (default 25), `offset`.

Summaries never include `html_template`; `html_chars` reports its size so an
agent can budget context before fetching. `get_social_template(template_id,
include_html=false)` returns the full spec with `html_omitted: true` — browse
specs cheaply, then re-fetch the chosen template with HTML.

### `list_social_template_facets`

Returns populated values with counts for: `formats`, `categories`,
`aspect_ratios`, `appearances`, `platforms`, `style_tags`, `use_when`,
`industries`.

## Filling a template (the consumer contract)

Both consumers — a Claude Desktop skill and an app-side LLM — follow the same
flow:

1. **Pick**: `list_social_templates(format=..., category=..., slides=N)` from
   the user's ask ("сделай карусель на 7 слайдов про X" → `format=carousel,
   slides=7`), then `get_social_template(id)`.
2. **Write content** per `content_brief` and each slot's `hint` /
   `max_chars` / `example`. `required: false` slots may be dropped (delete
   elements marked `data-optional="true"`).
3. **Expand repeatable slides**: duplicate each `data-repeat="true"` section
   to reach the desired count within `min_slides..max_slides`, filling each
   copy's slots (e.g. `point_number` 01, 02, …).
4. **Substitute**: replace `{{slot_name}}` tokens with the written text;
   replace the inner content of `data-slot` containers (list items, image)
   while keeping the container's classes.
5. **Re-skin (optional)**: override the 8 `:root` variables with brand tokens
   (e.g. from `get_palette` / `get_font_pair`).
6. **Render**: screenshot each `.slide` at its canvas size (headless browser)
   to produce the final post images.

## Examples

### Find a 7-slide educational carousel for a SaaS account

```json
list_social_templates {"format": "carousel", "category": "educational",
                       "industry": "saas", "slides": 7}
```

### Browse specs without pulling HTML into context

```json
get_social_template {"template_id": "social_carousel_pastel_listicle",
                     "include_html": false}
```

### Discover populated categories and platforms first

```json
list_social_template_facets {}
```
