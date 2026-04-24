-- ============================================================
-- Content Catalog — Charts / Landing Patterns / Icons
-- Migrates mcp-migration/*.csv into first-class catalog tables.
-- ============================================================

-- 16. chart_types (25 rows)
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

-- 17. landing_patterns (34 rows)
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

-- 18. icons (104 rows) — individual icons; complements existing icon_libraries
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
-- RLS — public read (consistent with base schema)
-- ============================================================

ALTER TABLE chart_types      ENABLE ROW LEVEL SECURITY;
ALTER TABLE landing_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE icons            ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public_read" ON chart_types;
CREATE POLICY "public_read" ON chart_types      FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "public_read" ON landing_patterns;
CREATE POLICY "public_read" ON landing_patterns FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "public_read" ON icons;
CREATE POLICY "public_read" ON icons            FOR SELECT TO anon, authenticated USING (true);
