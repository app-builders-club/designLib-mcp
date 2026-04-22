-- 004_dna_columns.sql
-- Adds dna/transformations/dna_overrides columns required by the dump.
-- Sourced from dump/db-dump/supabase-source/migrations/003_add_transformations_dna.sql.

ALTER TABLE design_styles      ADD COLUMN IF NOT EXISTS transformations jsonb;
ALTER TABLE domain_categories  ADD COLUMN IF NOT EXISTS dna             jsonb;
ALTER TABLE domains            ADD COLUMN IF NOT EXISTS dna_overrides   jsonb;
