-- ============================================================
-- designlib-mcp — combined schema for SELF-HOSTED Postgres
-- Merge of migrations 001..008 with all Supabase RLS removed
-- (no anon/authenticated roles on a plain Postgres; the app
--  connects directly as the DB owner, so "public_read" RLS is
--  unnecessary). Run once against an empty database.
-- ============================================================

-- ============================================================
-- 001 — base schema (15 tables + 3 views)
-- ============================================================

-- 1. style_families
CREATE TABLE style_families (
  id          TEXT PRIMARY KEY,
  name_en     TEXT NOT NULL,
  description TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. domain_categories
CREATE TABLE domain_categories (
  id           TEXT PRIMARY KEY,
  name_en      TEXT NOT NULL,
  description  TEXT,
  domain_count INTEGER NOT NULL DEFAULT 0,
  sort_order   INTEGER NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. font_pair_categories
CREATE TABLE font_pair_categories (
  id          TEXT PRIMARY KEY,
  name_en     TEXT NOT NULL,
  description TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. domains
CREATE TABLE domains (
  id           TEXT PRIMARY KEY,
  category_id  TEXT NOT NULL REFERENCES domain_categories(id) ON DELETE RESTRICT,
  name_en      TEXT NOT NULL,
  ui_patterns  TEXT[] NOT NULL DEFAULT '{}',
  tone         TEXT[] NOT NULL DEFAULT '{}',
  data_density TEXT NOT NULL,
  audience     TEXT NOT NULL,
  examples     TEXT[] NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_data_density CHECK (
    data_density IN ('very_high','high','medium_high','medium','low_medium','low')
  )
);

CREATE INDEX idx_domains_category ON domains(category_id);
CREATE INDEX idx_domains_data_density ON domains(data_density);

-- 5. design_styles
CREATE TABLE design_styles (
  id                  TEXT PRIMARY KEY,
  family_id           TEXT NOT NULL REFERENCES style_families(id) ON DELETE RESTRICT,
  name_en             TEXT NOT NULL,
  description         TEXT NOT NULL,
  visual_signatures   TEXT[] NOT NULL DEFAULT '{}',
  emotional_keywords  TEXT[] NOT NULL DEFAULT '{}',
  anti_patterns       TEXT[] NOT NULL DEFAULT '{}',
  tokens              JSONB NOT NULL,
  reference_products  JSONB NOT NULL DEFAULT '[]',
  domain_fit          JSONB NOT NULL DEFAULT '{}',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_design_styles_family ON design_styles(family_id);

-- 6. color_palettes
CREATE TABLE color_palettes (
  id              TEXT PRIMARY KEY,
  palette_type    TEXT NOT NULL,
  family_id       TEXT REFERENCES style_families(id) ON DELETE SET NULL,
  name            TEXT NOT NULL,
  colors          JSONB NOT NULL,
  tags            TEXT[] NOT NULL DEFAULT '{}',
  style_fit       TEXT[] NOT NULL DEFAULT '{}',
  wcag_aa         BOOLEAN,
  dark_mode_first BOOLEAN NOT NULL DEFAULT false,
  sort_order      INTEGER NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_palette_type CHECK (palette_type IN ('brand', 'collection'))
);

CREATE INDEX idx_color_palettes_type ON color_palettes(palette_type);
CREATE INDEX idx_color_palettes_family ON color_palettes(family_id) WHERE family_id IS NOT NULL;
CREATE INDEX idx_color_palettes_style_fit ON color_palettes USING GIN(style_fit);

-- 7. color_psychology
CREATE TABLE color_psychology (
  id                   TEXT PRIMARY KEY,
  name                 TEXT NOT NULL,
  name_en              TEXT NOT NULL,
  hue_range            INTEGER[] NOT NULL,
  emotions             TEXT[] NOT NULL DEFAULT '{}',
  psychological_effect TEXT NOT NULL,
  best_for             TEXT[] NOT NULL DEFAULT '{}',
  avoid_for            TEXT[] NOT NULL DEFAULT '{}',
  brands               TEXT[] NOT NULL DEFAULT '{}',
  family_affinity      JSONB NOT NULL DEFAULT '{}',
  ui_usage             JSONB NOT NULL DEFAULT '{}',
  real_product_usage   TEXT[] NOT NULL DEFAULT '{}',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. font_pairs
CREATE TABLE font_pairs (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  category_id    TEXT NOT NULL REFERENCES font_pair_categories(id) ON DELETE RESTRICT,
  heading        JSONB NOT NULL,
  body           JSONB NOT NULL,
  mono           JSONB,
  import_url     TEXT NOT NULL,
  size_kb        INTEGER NOT NULL,
  variable_font  BOOLEAN NOT NULL DEFAULT false,
  line_heights   JSONB NOT NULL,
  letter_spacing JSONB NOT NULL,
  mood           TEXT[] NOT NULL DEFAULT '{}',
  use_cases      TEXT[] NOT NULL DEFAULT '{}',
  style_fit      TEXT[] NOT NULL DEFAULT '{}',
  domain_fit     TEXT[] NOT NULL DEFAULT '{}',
  used_by        TEXT[] NOT NULL DEFAULT '{}',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_font_pairs_category ON font_pairs(category_id);
CREATE INDEX idx_font_pairs_style_fit ON font_pairs USING GIN(style_fit);

-- 9. icon_libraries
CREATE TABLE icon_libraries (
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  url             TEXT NOT NULL,
  license         TEXT NOT NULL,
  license_notes   TEXT,
  icon_count      INTEGER NOT NULL,
  icon_count_pro  INTEGER,
  total_variations INTEGER,
  icon_type       TEXT,
  packages        JSONB NOT NULL DEFAULT '{}',
  install         TEXT NOT NULL,
  import_example  TEXT NOT NULL,
  visual          JSONB NOT NULL,
  technical       JSONB NOT NULL,
  character       JSONB NOT NULL,
  tags            JSONB NOT NULL,
  notes           TEXT,
  unique_features JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 10. animation_presets
CREATE TABLE animation_presets (
  id                 TEXT PRIMARY KEY,
  category           TEXT NOT NULL,
  name               TEXT NOT NULL,
  description        TEXT,
  preview            TEXT,
  css                JSONB NOT NULL,
  tailwind           TEXT,
  framer_motion      JSONB NOT NULL,
  gsap               TEXT,
  parameters         JSONB NOT NULL DEFAULT '{}',
  intensity          TEXT,
  feel               TEXT[] DEFAULT '{}',
  style_fit          TEXT[] DEFAULT '{}',
  use_for            TEXT[] DEFAULT '{}',
  performance_impact TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_animation_category CHECK (
    category IN ('entrance','exit','hover','loading','microInteractions','decorative')
  )
);

CREATE INDEX idx_animation_presets_category ON animation_presets(category);

-- 11. animation_themed_collections
CREATE TABLE animation_themed_collections (
  id                    TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  description           TEXT,
  style_family_id       TEXT REFERENCES style_families(id) ON DELETE SET NULL,
  style_ids             TEXT[] NOT NULL DEFAULT '{}',
  characteristics       JSONB NOT NULL,
  included_animations   TEXT[] NOT NULL DEFAULT '{}',
  avoid_animations      TEXT[] NOT NULL DEFAULT '{}',
  optional_animations   TEXT[] DEFAULT '{}',
  css_variables         JSONB NOT NULL DEFAULT '{}',
  framer_motion_preset  JSONB NOT NULL DEFAULT '{}',
  real_evidence         JSONB,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 12. background_types
CREATE TABLE background_types (
  id              TEXT PRIMARY KEY,
  category        TEXT NOT NULL,
  name            TEXT NOT NULL,
  implementation  JSONB NOT NULL,
  customization   JSONB NOT NULL,
  character       JSONB NOT NULL,
  performance     JSONB NOT NULL,
  combinations    JSONB NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_bg_category CHECK (
    category IN ('solidsAndGradients','geometricPatterns','noiseAndTexture','decorative','specialEffects')
  )
);

CREATE INDEX idx_background_types_category ON background_types(category);

-- 13. ui_libraries
CREATE TABLE ui_libraries (
  id                    TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  framework             TEXT[] NOT NULL DEFAULT '{}',
  styling               TEXT NOT NULL,
  bundle_size           TEXT NOT NULL,
  bundle_size_note      TEXT,
  description           TEXT NOT NULL,
  pros                  TEXT[] NOT NULL DEFAULT '{}',
  cons                  TEXT[] NOT NULL DEFAULT '{}',
  install_command       TEXT NOT NULL,
  documentation         TEXT NOT NULL,
  variants              JSONB NOT NULL,
  style_recommendations TEXT[] NOT NULL DEFAULT '{}',
  best_for              TEXT[] NOT NULL DEFAULT '{}',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 14. recommendation_scores
CREATE TABLE recommendation_scores (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  matrix_type TEXT NOT NULL,
  key_a       TEXT NOT NULL,
  key_b       TEXT NOT NULL,
  score       INTEGER NOT NULL,
  refs        TEXT,

  CONSTRAINT valid_score CHECK (score BETWEEN -2 AND 2),
  CONSTRAINT valid_matrix_type CHECK (
    matrix_type IN ('style_domain', 'style_audience', 'style_tone')
  ),
  UNIQUE(matrix_type, key_a, key_b)
);

CREATE INDEX idx_rec_scores_lookup ON recommendation_scores(matrix_type, key_a);

-- 15. app_config
CREATE TABLE app_config (
  key         TEXT PRIMARY KEY,
  data        JSONB NOT NULL,
  description TEXT,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Views
CREATE VIEW domain_density_mapping AS
SELECT
  data_density,
  array_agg(id ORDER BY id) AS domain_ids
FROM domains
GROUP BY data_density;

CREATE VIEW domain_tone_mapping AS
SELECT
  tone_keyword,
  array_agg(d.id ORDER BY d.id) AS domain_ids
FROM domains d, unnest(d.tone) AS tone_keyword
GROUP BY tone_keyword;

CREATE VIEW style_family_counts AS
SELECT
  sf.id,
  sf.name_en,
  sf.description,
  sf.sort_order,
  COALESCE(c.cnt, 0)::INTEGER AS count
FROM style_families sf
LEFT JOIN (
  SELECT family_id, COUNT(*) AS cnt
  FROM design_styles
  GROUP BY family_id
) c ON c.family_id = sf.id
ORDER BY sf.sort_order;

-- ============================================================
-- 002 — platform discriminator
-- ============================================================
CREATE TYPE platform AS ENUM ('web', 'ios');

ALTER TABLE style_families ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE design_styles  ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE color_palettes ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE font_pairs     ADD COLUMN platform platform NOT NULL DEFAULT 'web';

CREATE INDEX idx_style_families_platform ON style_families(platform);
CREATE INDEX idx_design_styles_platform  ON design_styles(platform);
CREATE INDEX idx_color_palettes_platform ON color_palettes(platform);
CREATE INDEX idx_font_pairs_platform     ON font_pairs(platform);

-- ============================================================
-- 003 — iOS extensions (RLS removed)
-- ============================================================
ALTER TABLE design_styles ADD COLUMN ios_metadata JSONB;

CREATE TABLE ios_app_profiles (
  slug              TEXT PRIMARY KEY,
  family_id         TEXT REFERENCES style_families(id) ON DELETE SET NULL,
  aggregated        JSONB NOT NULL,
  screenshot_count  INTEGER,
  confidence        TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_confidence CHECK (confidence IN ('high','medium','low') OR confidence IS NULL)
);

CREATE INDEX idx_ios_app_profiles_family ON ios_app_profiles(family_id);

-- ============================================================
-- 004 — dna columns
-- ============================================================
ALTER TABLE design_styles      ADD COLUMN IF NOT EXISTS transformations jsonb;
ALTER TABLE domain_categories  ADD COLUMN IF NOT EXISTS dna             jsonb;
ALTER TABLE domains            ADD COLUMN IF NOT EXISTS dna_overrides   jsonb;

-- ============================================================
-- 005 — content catalog: chart_types / landing_patterns / icons (RLS removed)
-- ============================================================
CREATE TABLE IF NOT EXISTS chart_types (
  id                     TEXT PRIMARY KEY,
  data_type              TEXT NOT NULL,
  keywords               TEXT[] NOT NULL DEFAULT '{}',
  best_chart_type        TEXT NOT NULL,
  secondary_options      TEXT[] NOT NULL DEFAULT '{}',
  when_to_use            TEXT NOT NULL,
  when_not_to_use        TEXT NOT NULL,
  data_volume_threshold  TEXT,
  color_guidance         TEXT,
  a11y_grade             TEXT NOT NULL,
  a11y_notes             TEXT,
  a11y_fallback          TEXT,
  library_recommendation TEXT[] NOT NULL DEFAULT '{}',
  interactive_level      TEXT,
  sort_order             INTEGER NOT NULL DEFAULT 0,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_chart_a11y_grade CHECK (a11y_grade IN ('AAA','AA','A','B','C','D'))
);

CREATE INDEX IF NOT EXISTS idx_chart_types_keywords ON chart_types USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_chart_types_library  ON chart_types USING GIN(library_recommendation);
CREATE INDEX IF NOT EXISTS idx_chart_types_a11y     ON chart_types(a11y_grade);
CREATE INDEX IF NOT EXISTS idx_chart_types_data_type ON chart_types(data_type);

CREATE TABLE IF NOT EXISTS landing_patterns (
  id                      TEXT PRIMARY KEY,
  name                    TEXT NOT NULL,
  keywords                TEXT[] NOT NULL DEFAULT '{}',
  section_order           TEXT NOT NULL,
  primary_cta_placement   TEXT NOT NULL,
  color_strategy          TEXT,
  recommended_effects     TEXT,
  conversion_optimization TEXT,
  sort_order              INTEGER NOT NULL DEFAULT 0,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_landing_patterns_keywords ON landing_patterns USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_landing_patterns_cta      ON landing_patterns(primary_cta_placement);

CREATE TABLE IF NOT EXISTS icons (
  id           TEXT PRIMARY KEY,
  category     TEXT NOT NULL,
  icon_name    TEXT NOT NULL,
  keywords     TEXT[] NOT NULL DEFAULT '{}',
  library_id   TEXT REFERENCES icon_libraries(id) ON DELETE SET NULL,
  library_name TEXT NOT NULL,
  import_code  TEXT NOT NULL,
  usage        TEXT NOT NULL,
  best_for     TEXT,
  style        TEXT,
  sort_order   INTEGER NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_icons_category ON icons(category);
CREATE INDEX IF NOT EXISTS idx_icons_keywords ON icons USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_icons_library  ON icons(library_id) WHERE library_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_icons_style    ON icons(style);

-- ============================================================
-- 006 — inspiration_pages (RLS removed)
-- ============================================================
CREATE TABLE IF NOT EXISTS inspiration_pages (
  id                 TEXT PRIMARY KEY,
  source             TEXT NOT NULL,
  url_guess          TEXT,
  captured_at        DATE NOT NULL,
  screenshot_path    TEXT NOT NULL,

  page_type          TEXT NOT NULL,
  landing_pattern_id TEXT,
  style_family       TEXT,
  industry           TEXT,
  product_category   TEXT,
  audience           TEXT,
  appearance         TEXT NOT NULL,
  density            TEXT,
  mood               TEXT[] NOT NULL DEFAULT '{}',

  visual_signatures        TEXT[] NOT NULL DEFAULT '{}',
  keywords                 TEXT[] NOT NULL DEFAULT '{}',
  good_for_product_types   TEXT[] NOT NULL DEFAULT '{}',
  good_for_moods           TEXT[] NOT NULL DEFAULT '{}',
  good_for_stages          TEXT[] NOT NULL DEFAULT '{}',
  section_order            TEXT[] NOT NULL DEFAULT '{}',

  palette                  JSONB NOT NULL,
  typography               JSONB NOT NULL,
  primary_cta              JSONB,
  sections                 JSONB NOT NULL,
  inspiration_metadata     JSONB NOT NULL,
  reference_for            JSONB NOT NULL,
  effects                  JSONB NOT NULL DEFAULT '[]'::jsonb,
  interaction_cues         JSONB NOT NULL DEFAULT '[]'::jsonb,
  generation_constraints   JSONB,

  description              TEXT NOT NULL,
  why_it_works             TEXT NOT NULL,
  generation_prompt        TEXT,
  notes                    TEXT,

  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_page_type CHECK (page_type IN (
    'marketing_landing','about','blog_index','blog_post','careers',
    'ecommerce_home','portfolio','pricing','product_listing','product_page','signup'
  )),
  CONSTRAINT valid_appearance CHECK (appearance IN ('light','dark','mixed')),
  CONSTRAINT valid_density CHECK (density IS NULL OR density IN ('compact','comfortable','spacious')),

  CONSTRAINT landing_pattern_consistency CHECK (
    (page_type = 'marketing_landing' AND landing_pattern_id IS NOT NULL)
    OR (page_type <> 'marketing_landing' AND landing_pattern_id IS NULL)
  ),
  CONSTRAINT generation_consistency CHECK (
    (page_type IN ('marketing_landing','signup')
       AND generation_prompt IS NOT NULL
       AND generation_constraints IS NOT NULL)
    OR (page_type NOT IN ('marketing_landing','signup')
       AND generation_prompt IS NULL
       AND generation_constraints IS NULL)
  ),
  CONSTRAINT mood_count_2_6        CHECK (cardinality(mood) BETWEEN 2 AND 6),
  CONSTRAINT keywords_count_8_20   CHECK (cardinality(keywords) BETWEEN 8 AND 20),
  CONSTRAINT gfm_count_2_6         CHECK (cardinality(good_for_moods) BETWEEN 2 AND 6),
  CONSTRAINT gfpt_count_2_6        CHECK (cardinality(good_for_product_types) BETWEEN 2 AND 6),
  CONSTRAINT gfs_count_1_5         CHECK (cardinality(good_for_stages) BETWEEN 1 AND 5)
);

CREATE INDEX IF NOT EXISTS idx_insp_pages_page_type        ON inspiration_pages(page_type);
CREATE INDEX IF NOT EXISTS idx_insp_pages_landing_pattern  ON inspiration_pages(landing_pattern_id) WHERE landing_pattern_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_insp_pages_appearance       ON inspiration_pages(appearance);
CREATE INDEX IF NOT EXISTS idx_insp_pages_style_family     ON inspiration_pages(style_family);
CREATE INDEX IF NOT EXISTS idx_insp_pages_industry         ON inspiration_pages(industry);
CREATE INDEX IF NOT EXISTS idx_insp_pages_product_category ON inspiration_pages(product_category);
CREATE INDEX IF NOT EXISTS idx_insp_pages_density          ON inspiration_pages(density);

CREATE INDEX IF NOT EXISTS idx_insp_pages_mood             ON inspiration_pages USING GIN(mood);
CREATE INDEX IF NOT EXISTS idx_insp_pages_signatures       ON inspiration_pages USING GIN(visual_signatures);
CREATE INDEX IF NOT EXISTS idx_insp_pages_keywords         ON inspiration_pages USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_insp_pages_gf_product_types ON inspiration_pages USING GIN(good_for_product_types);
CREATE INDEX IF NOT EXISTS idx_insp_pages_gf_moods         ON inspiration_pages USING GIN(good_for_moods);
CREATE INDEX IF NOT EXISTS idx_insp_pages_gf_stages        ON inspiration_pages USING GIN(good_for_stages);
CREATE INDEX IF NOT EXISTS idx_insp_pages_section_order    ON inspiration_pages USING GIN(section_order);

-- ============================================================
-- 007 — inspiration_pages: use_when + relax generation_prompt
-- ============================================================
ALTER TABLE inspiration_pages
  ADD COLUMN IF NOT EXISTS use_when TEXT;

ALTER TABLE inspiration_pages
  DROP CONSTRAINT IF EXISTS generation_consistency;

ALTER TABLE inspiration_pages
  ADD CONSTRAINT generation_constraints_consistency CHECK (
    (page_type IN ('marketing_landing','signup')
       AND generation_constraints IS NOT NULL)
    OR (page_type NOT IN ('marketing_landing','signup')
       AND generation_constraints IS NULL)
  );

ALTER TABLE inspiration_pages
  ADD CONSTRAINT generation_prompt_required_for_landing_signup CHECK (
    page_type NOT IN ('marketing_landing','signup')
    OR generation_prompt IS NOT NULL
  );

-- ============================================================
-- 008 — animations (RLS removed)
-- ============================================================
CREATE TABLE IF NOT EXISTS animations (
  id                 TEXT PRIMARY KEY,
  title              TEXT NOT NULL,
  description        TEXT NOT NULL,
  use_when           TEXT[] NOT NULL DEFAULT '{}',
  category           TEXT NOT NULL,
  framework          TEXT NOT NULL,
  libraries          TEXT[] NOT NULL DEFAULT '{}',
  interactivity      TEXT NOT NULL,
  complexity         TEXT NOT NULL,
  style_tags         TEXT[] NOT NULL DEFAULT '{}',
  placement          TEXT[] NOT NULL DEFAULT '{}',
  keyword            TEXT[] NOT NULL DEFAULT '{}',
  component_filename TEXT NOT NULL,
  prompt_text        TEXT NOT NULL,
  source_file        TEXT NOT NULL,
  source_index       INTEGER NOT NULL,
  sort_order         INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT animations_category_valid CHECK (
    category IN ('background','hero','loader','text_effect','element',
                 'cursor_effect','overlay','decoration')
  ),
  CONSTRAINT animations_framework_valid CHECK (
    framework IN ('react','vanilla_html')
  ),
  CONSTRAINT animations_interactivity_valid CHECK (
    interactivity IN ('static','hover','click','cursor_track','scroll','mount_only')
  ),
  CONSTRAINT animations_complexity_valid CHECK (
    complexity IN ('light','medium','heavy')
  )
);

CREATE INDEX IF NOT EXISTS idx_animations_category    ON animations(category);
CREATE INDEX IF NOT EXISTS idx_animations_framework   ON animations(framework);
CREATE INDEX IF NOT EXISTS idx_animations_keyword     ON animations USING GIN(keyword);
CREATE INDEX IF NOT EXISTS idx_animations_use_when    ON animations USING GIN(use_when);
CREATE INDEX IF NOT EXISTS idx_animations_style_tags  ON animations USING GIN(style_tags);
CREATE INDEX IF NOT EXISTS idx_animations_libraries   ON animations USING GIN(libraries);
CREATE INDEX IF NOT EXISTS idx_animations_placement   ON animations USING GIN(placement);
