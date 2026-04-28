-- ============================================================
-- 007: inspiration_pages — add use_when + relax generation_prompt
-- ============================================================
-- TODO 1 (designlib-mcp-todo.md): backfill generation_prompt for the 9
-- non-landing/signup page_types. The old generation_consistency CHECK
-- forced generation_prompt to be NULL for those types, so it must be
-- relaxed before any row can carry a non-null value.
--
-- TODO 2: introduce a use_when TEXT column — prose "situational call"
-- the model uses to pick between candidates with overlapping tags.
--
-- generation_constraints (structural JSONB) stays tied to landing/signup
-- only — it encodes hard_rules/soft_guidance for full-page composition,
-- which only makes sense where there's a landing_pattern_id to anchor on.
-- ============================================================

ALTER TABLE inspiration_pages
  ADD COLUMN IF NOT EXISTS use_when TEXT;

-- Drop the old "all-or-nothing" constraint and replace with a narrower
-- one that only governs generation_constraints. generation_prompt is now
-- free to be filled for any page_type (still required for landing/signup).
ALTER TABLE inspiration_pages
  DROP CONSTRAINT IF EXISTS generation_consistency;

ALTER TABLE inspiration_pages
  ADD CONSTRAINT generation_constraints_consistency CHECK (
    (page_type IN ('marketing_landing','signup')
       AND generation_constraints IS NOT NULL)
    OR (page_type NOT IN ('marketing_landing','signup')
       AND generation_constraints IS NULL)
  );

-- Keep the existing invariant for landing/signup: a generation_prompt
-- must be present for these page_types. Non-landing/signup pages may
-- have it filled or null.
ALTER TABLE inspiration_pages
  ADD CONSTRAINT generation_prompt_required_for_landing_signup CHECK (
    page_type NOT IN ('marketing_landing','signup')
    OR generation_prompt IS NOT NULL
  );
