-- 003_ios_extensions.sql
-- iOS-specific fields and reference profile table.

ALTER TABLE design_styles ADD COLUMN ios_metadata JSONB;
-- ios_metadata shape (nullable for web, required for ios):
-- {
--   "liquid_glass_posture": "native_fit|selective|none|unclear",
--   "surfaces_affected": ["tab_bar","toolbar","modal_sheet",...],
--   "list_style_dominant": "inset_grouped|plain|card_grid|...",
--   "density_typical": "compact|comfortable|spacious",
--   "appearance_support": ["light","dark"] | ["light"] | ["dark"],
--   "corner_radius_cards_pt_median": 16,
--   "iconography": "sf_symbols_only|custom_glyph_set|mixed|photographic|unclear",
--   "reference_apps": ["linear","things_3","bear"]
-- }

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

ALTER TABLE ios_app_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON ios_app_profiles FOR SELECT TO anon, authenticated USING (true);
