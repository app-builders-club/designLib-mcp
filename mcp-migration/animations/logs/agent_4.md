# Agent 4 Log — Rows 91–120

**Scope**: animations3.md (source_index 25–44) + animations4.md (source_index 0–9)
**Total rows**: 30
**All files written**: Yes

---

## Results Table

| Row | source_file | source_index | staging_id | status |
|-----|-------------|-------------|-----------|--------|
| 91  | animations3.md | 25 | animation_animated_download | ✅ |
| 92  | animations3.md | 26 | animation_animate_card_animation | ✅ |
| 93  | animations3.md | 27 | animation_orbiting_carousel_with_animated_icons | ✅ |
| 94  | animations3.md | 28 | animation_hero_scrub | ✅ |
| 95  | animations3.md | 29 | animation_animated_testimonials | ✅ |
| 96  | animations3.md | 30 | animation_card_stack | ✅ |
| 97  | animations3.md | 31 | animation_warp_dialog | ✅ |
| 98  | animations3.md | 32 | animation_wireframe_dotted_globe | ✅ |
| 99  | animations3.md | 33 | animation_ethereal | ✅ |
| 100 | animations3.md | 34 | animation_animated_background_lines | ✅ |
| 101 | animations3.md | 35 | animation_animated_sign_in | ✅ |
| 102 | animations3.md | 36 | animation_testimonial_card | ✅ |
| 103 | animations3.md | 37 | animation_3_dots_loader | ✅ |
| 104 | animations3.md | 38 | animation_animated_video_on_scroll | ✅ |
| 105 | animations3.md | 39 | animation_halide_topo_hero | ✅ |
| 106 | animations3.md | 40 | animation_animated_characters_login_page | ✅ |
| 107 | animations3.md | 41 | animation_jelly_animated_hero | ✅ |
| 108 | animations3.md | 42 | animation_animated_gallery | ✅ |
| 109 | animations3.md | 43 | animation_currency_transfer_animation | ✅ |
| 110 | animations3.md | 44 | animation_remocn_perspective_marquee | ✅ |
| 111 | animations4.md | 0  | animation_animated_search_bar | ✅ |
| 112 | animations4.md | 1  | animation_animated_shader_hero | ✅ |
| 113 | animations4.md | 2  | animation_kinetic_team_hybrid | ✅ |
| 114 | animations4.md | 3  | animation_animated_input | ✅ |
| 115 | animations4.md | 4  | animation_modern_background_paths | ✅ |
| 116 | animations4.md | 5  | animation_svg_path_drawing_text_animation | ✅ |
| 117 | animations4.md | 6  | animation_cinematic_landing_hero_v2 | ✅ (ID collision — _v2 suffix applied) |
| 118 | animations4.md | 7  | animation_motion_footer | ✅ |
| 119 | animations4.md | 8  | animation_flip_countdown | ✅ |
| 120 | animations4.md | 9  | animation_animated_svg_text_path | ✅ |

---

## ID Collision

- **Row 117** (`animations4_006.md`): The natural ID `animation_cinematic_landing_hero` was already used by row 82 (`animations3_016.md`). Applied `_v2` suffix per PROTOCOL.md rules → `animation_cinematic_landing_hero_v2`.

---

## New Vocabulary Additions

These values were used in staging files but are NOT in the PROTOCOL.md seed lists. They should be reviewed for addition to the vocabulary.

### `style_tags` (open vocabulary — new values)
- `cinematic` — used by: animation_hero_scrub, animation_ethereal, animation_cinematic_landing_hero_v2, animation_motion_footer, animation_animated_shader_hero
- `topographic` — used by: animation_halide_topo_hero
- `cartoon` — used by: animation_animated_characters_login_page
- `wireframe` — used by: animation_wireframe_dotted_globe

### `placement` (open vocabulary — new values)
- `footer` — used by: animation_motion_footer

### `use_when` (open vocabulary — new values)
- `login_authentication_screen` — used by: animation_animated_characters_login_page
- `file_transfer_success` — used by: animation_currency_transfer_animation
- `payment_confirmation` — used by: animation_currency_transfer_animation
- `transaction_success_state` — used by: animation_currency_transfer_animation
- `countdown_display` — used by: animation_flip_countdown
- `launch_countdown` — used by: animation_flip_countdown
- `event_timer` — used by: animation_flip_countdown
- `brand_logo_showcase` — used by: animation_remocn_perspective_marquee
- `image_collection_reveal` — used by: animation_animated_gallery
- `portfolio_display` — used by: animation_animated_gallery
- `team_section` — used by: animation_kinetic_team_hybrid
- `about_page` — used by: animation_kinetic_team_hybrid
- `ai_chat_interface` — used by: animation_animated_input
- `search_input` — used by: animation_animated_input
- `onboarding_prompt` — used by: animation_animated_input
- `decorative_text_reveal` — used by: animation_svg_path_drawing_text_animation, animation_animated_svg_text_path
- `site_search` — used by: animation_animated_search_bar
- `command_palette` — used by: animation_animated_search_bar

---

## Issues / Observations

1. **Row 103 (`animation_3_dots_loader`)**: Source code uses `class=` instead of `className=` in JSX. Copied verbatim per PROTOCOL.md; bug noted under `## Notes`.

2. **Row 105 (`animation_halide_topo_hero`)**: The `/components/ui/halide-topo-hero.tsx` file in the source is a placeholder counter component. The actual Halide hero implementation is only in `demo.tsx`. Noted in staging JSON.

3. **Row 101 (`animation_animated_sign_in`)**: Contains a broken relative import `import "../../index.css"`. Noted in staging JSON.

4. **Row 100 (`animation_animated_background_lines`)**: Uses `<style jsx global>` which requires Next.js with styled-jsx. Noted in staging JSON.

5. **Row 107 (`animation_jelly_animated_hero`)**: Uses `data-aos` attributes requiring AOS library initialization in app root. Noted in staging JSON.

6. **Row 110 (`animation_remocn_perspective_marquee`)**: Uses `remotion`/`@remotion/player` — `useCurrentFrame` only works inside a Remotion composition. Not a standalone React component. Noted in staging JSON.

7. **Row 111 (`animation_animated_search_bar`)**: Source relies on non-Tailwind CSS class names (`.wrapper`, `.button-content`, etc.) that are not included in the source file. Noted in staging JSON.

8. **Row 112 (`animation_animated_shader_hero`)**: Uses `<style jsx>` for CSS keyframes — requires Next.js with styled-jsx. Also uses WebGL2. Noted in staging JSON.

9. **Row 120 (`animation_animated_svg_text_path`)**: Component has a dual-GSAP loading pattern (CDN script tag fallback + npm import) that may conflict. Noted in staging JSON.

10. **Complexity for row 117** (`animation_cinematic_landing_hero_v2`): Classified as `heavy` because it uses GSAP ScrollTrigger with a 7000px pinned scroll timeline — significantly more than a standard scroll animation.

11. **Libraries distinction**: Rows 97, 104, 108 use `motion` (npm package `motion`) not `framer-motion`. Correctly reflected in `libraries` arrays as `["motion"]`.
