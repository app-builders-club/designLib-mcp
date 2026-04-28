# Agent 1 Log — Rows 1–30 (source_index 0–29)

## Summary

Processed all 30 animation components from `animations.md` (source_index 0–29).
All 30 staging JSON files written to `mcp-migration/animations/staging/`.

---

## Files Written

| source_index | id | component_filename | category | complexity |
|---|---|---|---|---|
| 0 | animation_force_field_background | force-field-background.tsx | background | heavy |
| 1 | animation_jelly_squeeze | jelly-squeeze.tsx | element | heavy |
| 2 | animation_squares_background | squares-background.tsx | background | medium |
| 3 | animation_letter_glitch | letter-glitch.tsx | background | medium |
| 4 | animation_ballpit_background | ballpit-background.tsx | background | heavy |
| 5 | animation_grid_distortion | grid-distortion.tsx | background | heavy |
| 6 | animation_interactive_waves | interactive-waves-background.tsx | background | medium |
| 7 | animation_hyperspeed | hyperspeed.tsx | background | heavy |
| 8 | animation_faulty_terminal | faulty-terminal.tsx | background | heavy |
| 9 | animation_prismatic_burst | prismatic-burst.tsx | background | heavy |
| 10 | animation_lightning_background | lightning-background.tsx | background | heavy |
| 11 | animation_plasma | plasma.tsx | background | heavy |
| 12 | animation_gradient_blinds | gradient-blinds.tsx | background | heavy |
| 13 | animation_light_rays | light-rays.tsx | background | heavy |
| 14 | animation_floating_lines | floating-lines.tsx | background | heavy |
| 15 | animation_prism_background | prism-background.tsx | background | heavy |
| 16 | animation_liquid_ether | liquid-ether.tsx | background | heavy |
| 17 | animation_card_swap | card-swap.tsx | element | medium |
| 18 | animation_flying_posters | flying-posters.tsx | element | heavy |
| 19 | animation_interactive_folder | interactive-folder.tsx | element | medium |
| 20 | animation_masonry_gallery | masonry-gallery.tsx | element | medium |
| 21 | animation_tilted_card | tilted-card.tsx | element | medium |
| 22 | animation_ribbons | ribbons.tsx | cursor_effect | heavy |
| 23 | animation_ghost_cursor | ghost-cursor.tsx | cursor_effect | heavy |
| 24 | animation_laser_flow | laser-flow.tsx | background | heavy |
| 25 | animation_electric_border | electric-border.tsx | decoration | medium |
| 26 | animation_magnet_lines | magnet-lines.tsx | element | light |
| 27 | animation_gradual_blur | gradual-blur.tsx | decoration | light |
| 28 | animation_ascii_text | ascii-text.tsx | text_effect | heavy |
| 29 | animation_fuzzy_text | fuzzy-text.tsx | text_effect | medium |

---

## Decisions & Notes

### Framework
All 30 components use `framework: "react"` — the task description mentioned "raw HTML format" but every source file contains React TSX. Corrected consistently.

### Abbreviated prompt_text (long components)
The following components exceeded ~400 lines and used abbreviated placeholder code in prompt_text with a note pointing to the raw source file:
- `animation_hyperspeed` (source ~600 lines)
- `animation_liquid_ether` (source ~1087 lines)
- `animation_flying_posters` (source ~200 lines, but component body was a stub in the raw file itself)

All other components include full verbatim component code.

### Complexity rules applied
- Three.js / WebGL / OGL / p5.js → `heavy`
- GSAP / Framer Motion → `medium`
- Canvas-only (no Three.js) → `medium`
- Pure CSS / DOM manipulation (no canvas, no WebGL) → `light`

Exceptions:
- `animation_jelly_squeeze` (GSAP + 215-frame image sequence external loading) → `heavy` due to asset weight
- `animation_interactive_waves` (custom canvas Perlin noise, no Three.js) → `medium`

### New style_tags used (not in PROTOCOL seed list)
The following style_tags were introduced for semantic accuracy:
- `"fluid"` — used for wave/fluid simulation components (liquid_ether, interactive_waves)
- `"grid"` — used for grid-pattern components (squares_background, letter_glitch, magnet_lines)
- `"retro"` — used for ASCII/scanline aesthetics (ascii_text, fuzzy_text)

These should be added to PROTOCOL.md §5 vocabulary seeds.

### Category assignments
- `cursor_effect` used for components whose primary purpose is a cursor trail: `ribbons`, `ghost_cursor`
- `decoration` used for non-interactive overlays that wrap or frame content: `electric_border`, `gradual_blur`
- `text_effect` used for text-specific animations: `ascii_text`, `fuzzy_text`

### Libraries field
Components with no external dependencies beyond React use `"libraries": []`:
- `animation_electric_border` (canvas, no libs)
- `animation_magnet_lines` (DOM CSS, no libs)
- `animation_gradual_blur` (CSS backdrop-filter, no libs)
- `animation_fuzzy_text` (canvas, no libs)
- `animation_interactive_waves` (canvas, no libs)
- `animation_lightning_background` (raw WebGL, no external libs)

---

## Vocabulary Log (proposed additions to PROTOCOL.md §5)

### style_tags additions
- `"fluid"` — for fluid/wave/simulation animations
- `"grid"` — for tile or grid pattern visuals
- `"retro"` — for ASCII, scanline, CRT, or pixel aesthetics
