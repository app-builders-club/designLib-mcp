# Animations Standardization Protocol

**Read this BEFORE processing any prompt.** This file defines the exact format, the closed vocabularies, and the decision rules a subagent must follow when standardizing a raw prompt into a staging JSON record.

If you discover a value that doesn't fit any closed vocabulary, ADD it here under "Vocabulary log" before using it — never silently invent.

---

## 1. Workflow per prompt

You are dispatched with a **pre-assigned non-overlapping range** of `PROGRESS.md` row indices (e.g. "rows 1–20"). Operate ONLY on rows in your range — never touch rows outside it. This prevents Edit conflicts when multiple subagents run in parallel.

1. Open `mcp-migration/animations/raw/{source_stem}_{index:03d}.md` (e.g. `animations2_000.md`).
2. Read your row in `PROGRESS.md`. If status is `done`, skip. If `in_progress` (left over from a crashed run) or `todo`, claim it.
3. Mark the row `in_progress` with your subagent name in PROGRESS.md.
4. Extract the component:
   - Find the ` ```tsx ` / ` ```html ` fence after `Copy-paste this component to /components/ui folder:` (animations2/3/4) or after the descriptive paragraph (animations.md).
   - Capture the filename on the first line inside the fence (e.g. `aurora-background.tsx`). For animations.md raw HTML, derive a filename from the section's title (kebab-case) and use `.html`.
   - Capture the demo block if present (typically a second fence labelled `demo.tsx` or `App.tsx`).
   - Capture the `Install NPM dependencies` block (the bash fence).
5. Strip boilerplate:
   - The whole "You are given a task to integrate an existing React component / shadcn project structure / Tailwind CSS / Typescript / If it doesn't, provide instructions..." preamble.
   - "Copy-paste this component to /components/ui folder:" line and the filename line above the actual code.
   - "Implementation Guidelines" and "Steps to integrate" generic blocks at the end.
6. Author metadata:
   - **id** — `animation_<kebab-to-snake>` from filename, e.g. `animation_aurora_background`. Drop file extension. If duplicate exists in staging, append `_v2`, `_v3`, ...
   - **title** — Title Case of the component, e.g. "Aurora Background", "3D Folder", "Hyper-Speed Loader".
   - **description** — 1–2 sentences (max ~250 chars). Describe WHAT it is and the dominant visual idea. No fluff like "stunning" / "beautiful".
   - **use_when** — 3–5 bullets, each a normalized snake_case tag from the vocabulary below. If a fitting tag doesn't exist, add it to "Vocabulary log → use_when" below.
   - **keyword** — 5–10 free-form lowercase words/short phrases for search (component name parts, dominant colors, motion verbs, library names, motifs). Lowercase, no spaces inside a tag (use underscores). E.g. `["aurora","gradient","blurred","ambient","framer-motion","calm"]`.
7. Pick taxonomy values strictly from closed vocabularies (category / framework / interactivity / complexity). For style_tags / placement, use the seed list and add new values to "Vocabulary log" if needed.
8. Build `prompt_text` per the template in section 2.
9. Write `mcp-migration/animations/staging/{id}.json` (schema in section 3).
10. Set PROGRESS.md row to `done`. If you can't classify confidently, set `needs_review` with a one-line reason in the Notes column. If the prompt has no extractable code, set `skipped` with reason `no_code` in Notes.

---

## 2. prompt_text template (exact shape)

````markdown
# {title}

{description}

## Use when
- {use_when[0] rephrased to a human sentence}
- {use_when[1] rephrased ...}

## Stack
- Framework: {react | vanilla-html}
- Libraries: {libs comma-separated, or "none"}
- Requires: {tailwind, shadcn, ...}     ← omit this whole line if none

## Install
```bash
{exact contents of the original Install fence; "none" if no deps}
```

## Component — {filename}
```tsx
{verbatim component code}
```

## Demo
```tsx
{verbatim demo code}
```

## Notes
- {only include section if there are real caveats: external assets, perf, SSR, browser support}
````

Rules:
- "Use when" bullets are HUMAN-readable sentences expanded from the use_when tag (e.g. tag `loading_data` → bullet "Showing the user that data is being fetched and they should wait."). Keep tags structured for search; bullets readable for humans.
- Code fences inside `prompt_text` use triple backticks. The catalog README documents that `prompt_text` itself is markdown.
- Do NOT modify component code. No formatting, no rename, no import cleanup. Even if it looks broken, copy it as-is and note the issue under `## Notes`.
- For animations.md raw-HTML prompts: replace the `## Component — *.tsx` fence with `## Component — {filename}.html` and use ` ```html ` instead of ` ```tsx `. Demo section often won't apply — omit it.
- If the original prompt embedded both component code AND demo in a single fence (separator like `// demo.tsx` comment), split them into two fences.

---

## 3. Staging JSON schema

```json
{
  "id": "animation_aurora_background",
  "title": "Aurora Background",
  "description": "Soft aurora-like blurred gradient bands drifting across the viewport, used as a calming page background.",
  "use_when": ["dark_landing_page", "brand_personality_calm", "value_proposition_emphasis"],
  "category": "background",
  "framework": "react",
  "libraries": ["framer-motion"],
  "interactivity": "static",
  "complexity": "light",
  "style_tags": ["aurora", "gradient", "glass", "dark"],
  "placement": ["hero", "background"],
  "keyword": ["aurora","gradient","blurred","ambient","calm","dark","framer-motion"],
  "component_filename": "aurora-background.tsx",
  "prompt_text": "# Aurora Background\n\n...",
  "source_file": "animations2.md",
  "source_index": 9
}
```

All array fields lowercase, snake_case. `id` and `component_filename` are the only fields where casing/dashes matter.

---

## 4. Closed vocabularies

### category (single)
`background`, `hero`, `loader`, `text_effect`, `element`, `cursor_effect`, `overlay`, `decoration`.

If a prompt fits NONE → add a new value under "Vocabulary log → category" with one-line definition, then use it.

### framework (single)
`react`, `vanilla_html`. No others.

### interactivity (single)
`static`, `hover`, `click`, `cursor_track`, `scroll`, `mount_only`. Pick the dominant one. If a component reacts to BOTH cursor and click, prefer `cursor_track` (the continuous one).

### complexity (single)
- `light` — pure CSS or minimal Framer, no third-party runtime > 30 KB
- `medium` — Framer Motion, standard React, total bundle < 100 KB
- `heavy` — Three.js / R3F / WebGL / shaders / large bundle > 100 KB

When unsure between two, pick the heavier.

---

## 5. Open-ish vocabularies (extend as needed; log additions)

### style_tags (multi)
Seed: `neon`, `cyber`, `futuristic`, `minimal`, `glass`, `gradient`, `geometric`, `particle`, `3d`, `aurora`, `organic`, `monochrome`, `colorful`, `dark`, `light`, `retro`, `glitch`.

### placement (multi)
Seed: `hero`, `background`, `section`, `inline`, `loading_screen`, `card`, `cta`, `modal`, `nav`, `footer`.

### use_when (multi, normalized situation tags)
Seed: `first_load_reveal`, `value_proposition_emphasis`, `loading_data`, `system_thinking`, `success_celebration`, `error_state`, `404_page`, `empty_state`, `cta_attention`, `brand_personality_playful`, `brand_personality_serious`, `brand_personality_calm`, `dark_landing_page`, `product_showcase`, `text_emphasis`, `interactive_demo`, `visual_break_between_sections`, `data_visualization_emphasis`, `decorative_filler`.

Reuse existing tags wherever possible — the whole point of `use_when` is that one situation maps to many animations.

---

## 6. Vocabulary log

Append entries here when you introduce a new value. One line each.

### category additions
- _(none — all 120 prompts fit the closed vocabulary)_

### style_tags additions
- `fluid` — fluid / wave / simulation animations (agent 1: liquid_ether, interactive_waves)
- `grid` — tile or grid-pattern visuals (agent 1: squares_background, letter_glitch, magnet_lines)
- `retro` — ASCII, scanline, CRT, pixel aesthetics (agent 1: ascii_text, fuzzy_text)
- `cinematic` — hero/landing animations with film-like pacing or pinned scroll (agent 4: hero_scrub, ethereal, cinematic_landing_hero_v2, motion_footer, animated_shader_hero)
- `topographic` — contour/topographic-line motifs (agent 4: halide_topo_hero)
- `cartoon` — cartoon/illustration aesthetic (agent 4: animated_characters_login_page)
- `wireframe` — wireframe/line-art aesthetic (agent 4: wireframe_dotted_globe)
- `shiny` — shimmering gradient sweep on text/surfaces (agent 3: shiny_text)
- `shader` — GLSL/WebGL fragment-shader-driven visuals (agent 3: animated_shader_background)
- `split` — split-pane / split-screen compositions (agent 3: animated_scroll)
- `fullscreen` — fills the viewport / full-bleed (agent 3: animated_scroll)
- `globe` — globe / planet / orb visualizations (agent 3: interactive_globe)
- `stagger` — per-character or per-item staggered animation (agent 3: animated_slideshow)
- `clip_path` — uses CSS clip-path for reveal/transition (agent 3: animated_slideshow)
- `chart` — chart-like bar/line/data-grid visuals (agent 3: animated_card_v2)

### placement additions
- `footer` — bottom-of-page placement, distinct from `section` (agent 4: motion_footer)

### use_when additions
- `login_authentication_screen` — sign-in / login surfaces (agent 4: animated_characters_login_page)
- `file_transfer_success` — completed file/data transfers (agent 4: currency_transfer_animation)
- `payment_confirmation` — successful payment / checkout (agent 4: currency_transfer_animation)
- `transaction_success_state` — generic transaction-success confirmation (agent 4: currency_transfer_animation)
- `countdown_display` — countdown timer surfaces (agent 4: flip_countdown)
- `launch_countdown` — pre-launch / coming-soon countdowns (agent 4: flip_countdown)
- `event_timer` — event countdown timers (agent 4: flip_countdown)
- `brand_logo_showcase` — logo wall / partner marquee (agent 4: remocn_perspective_marquee)
- `image_collection_reveal` — animated image grid/gallery reveals (agent 4: animated_gallery)
- `portfolio_display` — portfolio / case-study sections (agent 4: animated_gallery)
- `team_section` — team / about-us sections (agent 4: kinetic_team_hybrid)
- `about_page` — about / company-page surfaces (agent 4: kinetic_team_hybrid)
- `ai_chat_interface` — AI chat / messaging UIs (agent 4: animated_input)
- `search_input` — search input fields (agent 4: animated_input)
- `onboarding_prompt` — onboarding / first-run prompts (agent 4: animated_input)
- `decorative_text_reveal` — decorative SVG-stroke / path text reveals (agent 4: svg_path_drawing_text_animation, animated_svg_text_path)
- `site_search` — site-wide search bar surfaces (agent 4: animated_search_bar)
- `command_palette` — command palette / quick-action surfaces (agent 4: animated_search_bar)

### Notes / edge cases
- Row 31 (`animations_030.md`) bundled three components (ShinyText, Aurora, plus free-form prompt fragments). Only the first component (ShinyText) was captured; Aurora was already covered by `animation_aurora_background` (animations2.md row 41).
- Row 90 (`animations3_024.md`) collided on natural ID `animation_animated_card` with row 68; resolved with `_v2` suffix per §1 step 6. Same filename, different component (Tailwind chart-grid hover-reveal vs framer-motion 3D-tilt job card).
- Row 117 (`animations4_006.md`) collided on natural ID `animation_cinematic_landing_hero` with row 82; resolved with `_v2` suffix.
- Row 48 (`animations2_016.md`) was an exact duplicate of row 47; second copy renamed to `animation_etheral_shadow_v2` (typo `etheral` preserved verbatim from source).
- Row 42 (`animations2_002.md`) had a typo `intereactive` in the raw filename — staging ID corrected to `animation_stacked_panels_cursor_interactive`.
- Source-code typos (e.g. `class=` instead of `className=` on row 103) are preserved verbatim per §2 rule 3, with the bug noted in `prompt_text` `## Notes`.
- Three long animations.md components (`hyperspeed`, `liquid_ether`, `flying_posters`) used abbreviated `prompt_text` with a pointer to the raw file — agent 1 decision; revisit if full inline copy is preferred.
