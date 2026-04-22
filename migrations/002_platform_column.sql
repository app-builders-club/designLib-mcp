-- 002_platform_column.sql
-- Adds platform discriminator across catalog tables.

CREATE TYPE platform AS ENUM ('web', 'ios');

ALTER TABLE style_families ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE design_styles  ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE color_palettes ADD COLUMN platform platform NOT NULL DEFAULT 'web';
ALTER TABLE font_pairs     ADD COLUMN platform platform NOT NULL DEFAULT 'web';

CREATE INDEX idx_style_families_platform ON style_families(platform);
CREATE INDEX idx_design_styles_platform  ON design_styles(platform);
CREATE INDEX idx_color_palettes_platform ON color_palettes(platform);
CREATE INDEX idx_font_pairs_platform     ON font_pairs(platform);
