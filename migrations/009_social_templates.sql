-- ============================================================
-- Social media design templates (stories + carousels)
--
-- NOTE: unlike 001-008 this migration has NO Supabase RLS block.
-- The project runs on plain Postgres (Hetzner/Coolify) where the
-- anon/authenticated roles do not exist; CREATE POLICY would fail.
-- ============================================================

CREATE TABLE IF NOT EXISTS social_templates (
  id             TEXT PRIMARY KEY,          -- social_<format>_<descriptor>
  title          TEXT NOT NULL,
  description    TEXT NOT NULL,             -- 2-4 sentences: what it is + dominant visual idea
  why_it_works   TEXT NOT NULL,             -- 2-4 sentences: why this pattern performs
  content_brief  TEXT NOT NULL,             -- guidance for the filling LLM: tone, hook formula, CTA advice

  -- classification (filterable scalars)
  format         TEXT NOT NULL,             -- story | carousel
  aspect_ratio   TEXT NOT NULL,             -- 9:16 (1080x1920) | 4:5 (1080x1350) | 1:1 (1080x1080)
  appearance     TEXT NOT NULL,             -- light | dark | mixed
  category       TEXT NOT NULL,             -- content purpose, see CHECK below

  -- slide handling (variable-length via repeatable slides in `slides` JSONB)
  slide_count    INTEGER NOT NULL,          -- slides authored in html_template
  min_slides     INTEGER NOT NULL,          -- allowed range after removing/duplicating
  max_slides     INTEGER NOT NULL,          --   repeatable slides; fixed template => min=max=count

  -- tag arrays (GIN)
  platform_fit   TEXT[] NOT NULL DEFAULT '{}',   -- closed: instagram|tiktok|linkedin|facebook
  style_tags     TEXT[] NOT NULL DEFAULT '{}',   -- open vocab: pastel, brutalist, neon_gradient, ...
  use_when       TEXT[] NOT NULL DEFAULT '{}',   -- snake_case situations: launch_announcement, ...
  keywords       TEXT[] NOT NULL DEFAULT '{}',   -- free search words, lowercased
  industry_fit   TEXT[] NOT NULL DEFAULT '{}',   -- fitness, beauty, saas, ecommerce, creator, ...

  -- structured content
  slides         JSONB NOT NULL,            -- ordered [{index, role, layout_note, repeatable, slots:[...]}]
  fonts          JSONB NOT NULL,            -- [{role, family, google_font, weights, fallback}]

  -- the renderable artifact: one self-contained HTML doc, all slides as
  -- <section class="slide" data-slide="N" data-role="...">; {{slot}} tokens
  -- for text, data-slot="..." for structural slots; :root token contract
  html_template  TEXT NOT NULL,

  -- provenance (pattern inspiration only; markup and copy are original)
  source         TEXT NOT NULL DEFAULT 'original',
  source_url     TEXT,
  source_note    TEXT,
  preview_path   TEXT,                      -- local render path; not served

  sort_order     INTEGER NOT NULL DEFAULT 0,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT social_templates_format_valid CHECK (format IN ('story','carousel')),
  CONSTRAINT social_templates_aspect_ratio_valid CHECK (aspect_ratio IN ('9:16','4:5','1:1')),
  CONSTRAINT social_templates_format_ratio_valid CHECK (
    (format = 'story' AND aspect_ratio = '9:16') OR format = 'carousel'
  ),
  CONSTRAINT social_templates_appearance_valid CHECK (appearance IN ('light','dark','mixed')),
  CONSTRAINT social_templates_category_valid CHECK (
    category IN ('promo','product_showcase','educational','listicle','checklist',
                 'quote','announcement','testimonial','personal_story','before_after',
                 'event','engagement')
  ),
  CONSTRAINT social_templates_slide_bounds_valid CHECK (
    min_slides >= 1 AND min_slides <= slide_count
    AND slide_count <= max_slides AND max_slides <= 20
  ),
  CONSTRAINT social_templates_platform_fit_valid CHECK (
    platform_fit <@ ARRAY['instagram','tiktok','linkedin','facebook']::text[]
  ),
  CONSTRAINT social_templates_source_valid CHECK (
    source IN ('canva_gallery','adobe_express_gallery','dribbble','behance','original','other')
  )
);

CREATE INDEX IF NOT EXISTS idx_soctpl_format       ON social_templates(format);
CREATE INDEX IF NOT EXISTS idx_soctpl_category     ON social_templates(category);
CREATE INDEX IF NOT EXISTS idx_soctpl_aspect_ratio ON social_templates(aspect_ratio);
CREATE INDEX IF NOT EXISTS idx_soctpl_appearance   ON social_templates(appearance);
CREATE INDEX IF NOT EXISTS idx_soctpl_min_slides   ON social_templates(min_slides);
CREATE INDEX IF NOT EXISTS idx_soctpl_max_slides   ON social_templates(max_slides);
CREATE INDEX IF NOT EXISTS idx_soctpl_platform_fit ON social_templates USING GIN(platform_fit);
CREATE INDEX IF NOT EXISTS idx_soctpl_style_tags   ON social_templates USING GIN(style_tags);
CREATE INDEX IF NOT EXISTS idx_soctpl_use_when     ON social_templates USING GIN(use_when);
CREATE INDEX IF NOT EXISTS idx_soctpl_keywords     ON social_templates USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_soctpl_industry_fit ON social_templates USING GIN(industry_fit);
