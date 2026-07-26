# Social Templates Collection Protocol

**Read this BEFORE processing any template.** This file defines the workflow, the exact record format, the HTML contract, the legal rules, and the closed vocabularies an agent must follow when turning a template-gallery reference into a staging JSON record.

If you discover a value that doesn't fit any open vocabulary seed list, ADD it under "Vocabulary log" before using it — never silently invent. Closed vocabularies (format, aspect_ratio, appearance, category, platform_fit, slide roles, slot types, source) are frozen: if nothing fits, set `needs_review`, don't extend them.

---

## 0. Legal rules (non-negotiable)

The reference (Canva/Adobe Express/Dribbble/Behance preview) is used to learn the **structural pattern**: grid, hierarchy, slide rhythm, color strategy, type-scale contrast. The record you produce must be an **original work**:

- NEVER copy text from the reference. All placeholder copy (`example` values, HTML placeholder content) is written by you, in English, realistic but generic.
- NEVER trace, embed, screenshot-crop, or base64 any imagery from the reference. Image areas become `image_slot`s with neutral placeholder styling (gradient/diagonal-stripe div).
- NEVER reproduce brand names, logos, handles, or recognizable brand color+type combinations from the reference.
- `source_url` records where the PATTERN was observed — provenance only. Reference screenshots live in `refs/` which is gitignored and never enters the DB.
- The self-check render (§5) doubles as a distance check: your render must read as *the same layout pattern, visibly different execution*. If it looks like a copy, redesign the styling before staging. If similarity still feels high, set `needs_review` with a note.

---

## 1. Workflow per template

You are dispatched with a **pre-assigned non-overlapping range** of `PROGRESS.md` row indices (e.g. "rows 1–15"). Operate ONLY on rows in your range — never touch rows outside it. This prevents Edit conflicts when multiple agents run in parallel.

1. Read your row in `PROGRESS.md`. If status is `done`, skip. If `in_progress` (leftover from a crashed run) or `todo`, claim it: set `in_progress` with your agent name.
2. Open the reference screenshot `refs/{ref_png}` and analyze it with `ANALYSIS_PROMPT.md`. The output is the metadata + slides/slots spec (everything except `html_template`).
3. Author the HTML template per the contract in §3. Original markup, original placeholder copy, tokens via CSS custom properties.
4. Self-check render (§5). Fix and re-render — at most 2 fix loops, then `needs_review` with a reason.
5. Write `staging/{id}.json` (schema in §2). Keys must exactly match the SQL columns of `social_templates` (see `migrations/009_social_templates.sql`).
6. Validate your record: `python scripts/emit_social_templates_sql.py --dry-run` must report it valid.
7. Set your PROGRESS.md row to `done` (fill the `template_id` column). If you can't classify confidently → `needs_review` + one-line reason in Notes. If the reference is unusable (unreadable, watermarked to death, duplicate of an existing template) → `skipped` + reason.

Statuses: `todo → in_progress → done | needs_review | skipped`.

---

## 2. Staging JSON schema

One file per record: `staging/{id}.json`. All array values lowercase snake_case (keywords may be plain lowercase words). See `tests/scripts/fixtures/social_template_staging_sample.json` for a complete valid example.

```json
{
  "id": "social_carousel_pastel_listicle",
  "title": "Pastel Listicle Carousel",
  "description": "2-4 sentences: what it is + the dominant visual idea. No fluff ('stunning', 'beautiful').",
  "why_it_works": "2-4 sentences: why this pattern performs on feed/stories (attention mechanics, readability, swipe logic).",
  "content_brief": "Guidance for the LLM that will fill it: tone, hook formula, per-slide content discipline, CTA advice.",
  "format": "carousel",
  "aspect_ratio": "4:5",
  "appearance": "light",
  "category": "listicle",
  "slide_count": 3,
  "min_slides": 3,
  "max_slides": 8,
  "platform_fit": ["instagram", "linkedin"],
  "style_tags": ["pastel", "rounded", "soft_shadow"],
  "use_when": ["tips_series", "audience_education"],
  "keywords": ["listicle", "pastel", "tips", "carousel"],
  "industry_fit": ["creator", "beauty"],
  "slides": [
    {
      "index": 1,
      "role": "hook",
      "layout_note": "One-sentence structural description of the slide layout.",
      "repeatable": false,
      "slots": [
        {"name": "hook_headline", "type": "headline", "max_chars": 60, "required": true,
         "hint": "What the filling LLM should write here.", "example": "A realistic example."}
      ]
    }
  ],
  "fonts": [
    {"role": "display", "family": "Archivo Black", "google_font": true, "weights": [400], "fallback": "sans-serif"},
    {"role": "body", "family": "Inter", "google_font": true, "weights": [400, 600], "fallback": "sans-serif"}
  ],
  "html_template": "<link ...><style>:root{...}</style><section class=\"slide\" ...>...</section>",
  "source": "canva_gallery",
  "source_url": "https://www.canva.com/templates/...",
  "source_note": "Layout rhythm inspired by the reference; all markup and copy original.",
  "preview_path": "mcp-migration/social-templates/renders/social_carousel_pastel_listicle_1.png"
}
```

Field discipline:
- **id** — `social_<format>_<descriptor>`, snake_case, unique across staging. Descriptor names the pattern, not the source (`social_story_bold_promo`, not `social_story_canva_123`).
- **description / why_it_works** — 2-4 flat sentences each. NO size adjectives (small/large/oversized) — use structural words (display-scale, full-bleed, lower-third).
- **content_brief** — imperative, addressed to the filling LLM. Include character discipline ("keep hook under 60 chars"), tone, and what NOT to write.
- **slide_count / min_slides / max_slides** — count = slides authored in HTML; min/max = allowed after deleting/duplicating `repeatable` slides. Fixed template → min = count = max. A variable range REQUIRES at least one `"repeatable": true` slide.
- **slots** — every fillable zone. `name` unique across the whole template (it IS the placeholder token). Every text slot needs `max_chars` sized to the layout (measure what fits, don't guess generously — overflow is the #1 render failure).
- **fonts** — mirrors the Google Fonts `<link>` in the HTML. Every family used must be listed with a fallback stack.

---

## 3. HTML contract

One self-contained HTML document per template:

- All slides as sibling `<section class="slide" data-slide="N" data-role="{role}">` elements. Shared `<style>` block on top; Google Fonts via `<link>` allowed.
- Fixed canvas per slide: `9:16` → 1080×1920, `4:5` → 1080×1350, `1:1` → 1080×1080 (`width`/`height` in px on `.slide`).
- Repeatable slides carry `data-repeat="true"` — the filling LLM duplicates/removes these sections.
- **Placeholders:**
  - Text slots: `{{slot_name}}` moustache token inline in the markup.
  - Structural slots (`image_slot`, `bullet_list`, `avatar_slot`, `logo_slot`): `data-slot="slot_name"` on the container, with generic placeholder content inside (neutral gradient div for images, sample `<li>`s for lists).
  - Optional elements: `data-optional="true"` — the filler may delete them.
  - The set of `{{tokens}}` + `data-slot` names must EXACTLY equal the declared slot names (the validator enforces both directions).
- **Token contract (mandatory):** `:root` defines at minimum
  `--bg, --surface, --accent, --accent-contrast, --text-primary, --text-secondary, --font-display, --font-body`.
  Colors and fonts are referenced ONLY via `var()` — this is how a consuming LLM re-skins the template to a brand by overriding 8 variables. Pure white/black overlay exceptions allowed (e.g. `rgba(0,0,0,.4)` scrims).
- Every `--font-*` var includes the fallback stack (`'Inter', sans-serif`).
- Pagination indicators ("2/7", dots) are rendered by the template itself — NOT a slot.
- Size budget: target ≤ 12,000 chars, hard cap 20,000. No base64 payloads, no external assets besides Google Fonts.
- No JavaScript. Static CSS only (gradients, borders, shadows, transforms are fine).

---

## 4. Authoring metadata

- **category** (closed, single): `promo · product_showcase · educational · listicle · checklist · quote · announcement · testimonial · personal_story · before_after · event · engagement`. A "hook" is a slide role, not a category.
- **format/aspect_ratio**: story → always `9:16`. Carousel → `4:5` (feed-optimal) or `1:1`.
- **appearance**: dominant scheme of the template as authored: `light · dark · mixed` (mixed = alternating light/dark slides).
- **platform_fit** (closed): `instagram · tiktok · linkedin · facebook`. Stories → instagram/tiktok (facebook if generic). Text-heavy educational carousels → add linkedin.
- **style_tags** (open, seeded): visual DNA, see Vocabulary log seed. 2-6 values.
- **use_when** (open, seeded): situations, see Vocabulary log seed. 2-5 values.
- **keywords** (free): 4-12 lowercase search words: format synonyms, motifs, colors, moods.
- **industry_fit** (open, seeded): keep BROAD (`fitness`, not `crossfit_box_owners`). 1-5 values.
- **slide roles** (closed): `hook` (first, stops the swipe) · `content` (the substance) · `proof` (stats, testimonials, results) · `recap` (summary list) · `cta` (follow/save/link).
- **slot types** (closed): `headline · subhead · body · bullet_list · cta · kicker · quote · stat · badge · handle · image_slot · avatar_slot · logo_slot`.

---

## 5. Self-check render (mandatory)

1. Write your HTML to a temp file and open it via `file://` with playwright-cli.
2. Screenshot each `.slide` element → `renders/{id}_{n}.png` (set viewport to the slide canvas size; there is no JS, so no waiting needed).
3. Inspect the renders:
   - No text overflow or clipping at the declared `max_chars` (test with the longest `example` values).
   - Every slot visually present and readable; contrast between text and its background holds.
   - Composition matches your `layout_note`s.
   - Side-by-side with the ref: same pattern, visibly NOT a copy (§0).
4. Fix → re-render. Max 2 loops; still broken → `needs_review`.
5. Record the first render path in `preview_path`.

---

## 6. Vocabulary log (append-only)

Add a bullet `value — one-line definition (agent N)` before first use. Do not remove or rename existing entries.

### style_tags seed
`bold_type` · `pastel` · `neon_gradient` · `brutalist` · `minimal` · `rounded` · `soft_shadow` · `hard_shadow` · `monochrome` · `duotone` · `editorial_serif` · `handwritten_accent` · `grain_texture` · `sticker_elements` · `outlined_type` · `full_bleed_photo` · `collage` · `grid_lines` · `torn_paper` · `glassmorphism`

### use_when seed
`product_launch` · `sale_promotion` · `tips_series` · `audience_education` · `brand_storytelling` · `social_proof` · `event_invite` · `community_engagement` · `content_repurposing` · `lead_generation` · `behind_the_scenes` · `weekly_series`

### industry_fit seed
`saas` · `ecommerce` · `creator` · `fitness` · `beauty` · `food` · `travel` · `finance` · `education` · `real_estate` · `healthcare` · `agency` · `fashion` · `local_business`

### New values
(append below)

- `monospace_type` — type system built on a fixed-width family, letters aligned on a character grid (agent collector-figma-1)
- `retro_terminal` — command-line aesthetic: prompt lines, line numbers, block cursor, scanline overlay (agent collector-figma-1)
- `pixel_ui` — vintage operating-system chrome rebuilt in CSS: bevelled frames, title bars, dialog buttons (agent collector-figma-1)
