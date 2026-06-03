from __future__ import annotations
from collections import Counter
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from designlib_mcp.config import Settings
from designlib_mcp.models.common import Platform
from designlib_mcp.repository.normalizer import (
    _to_style_summary, _to_style_full,
    _to_palette_summary, _to_palette_full,
    _to_font_pair_summary, _to_font_pair_full,
    _to_domain_summary, _to_domain_full,
    _to_chart_type_summary, _to_chart_type_full,
    _to_landing_pattern_summary, _to_landing_pattern_full,
    _to_icon_summary, _to_icon_full,
    _to_inspiration_page_summary, _to_inspiration_page_full,
    _to_animation_summary, _to_animation_full,
)


class PostgresRepository:
    """Read-only catalog access against a plain Postgres via psycopg.

    Drop-in replacement for the former Supabase/PostgREST repository: method
    signatures and return shapes are identical, so tools/, cross_links and the
    normalizer are unchanged. PostgREST query-builder calls are translated to
    SQL — array filters use `@>`, JSON paths use `->>`, `count="exact"` becomes
    a `count(*) OVER()` window column.
    """

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    @classmethod
    def from_settings(cls, settings: Settings) -> "PostgresRepository":
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is required")
        pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=True,
        )
        return cls(pool)

    # -------------------------------------------------------------------------
    # Low-level helpers
    # -------------------------------------------------------------------------

    def _all(self, sql: str, params: list[Any] | tuple = ()) -> list[dict]:
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _one(self, sql: str, params: list[Any] | tuple = ()) -> dict | None:
        rows = self._all(sql, params)
        return rows[0] if rows else None

    @staticmethod
    def _total(rows: list[dict]) -> int:
        return rows[0]["total_count"] if rows else 0

    def health_check(self) -> bool:
        return bool(self._one("SELECT 1 AS ok"))

    # -------------------------------------------------------------------------
    # Styles
    # -------------------------------------------------------------------------

    def list_styles(
        self, platform: Platform, *,
        family: str | None = None, appearance: str | None = None,
        tone: str | None = None, density: str | None = None,
        tags: list[str] | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["platform::text = %s"]
        params: list[Any] = [platform.value]
        if family:
            conds.append("family_id = %s")
            params.append(family)
        if tone:
            conds.append("emotional_keywords @> %s")
            params.append([tone])
        if density:
            if platform == Platform.IOS:
                conds.append("ios_metadata->>'density_typical' = %s")
            else:
                conds.append("tokens->'layout'->>'density' = %s")
            params.append(density)
        if tags:
            for t in tags:
                conds.append("(visual_signatures @> %s OR emotional_keywords @> %s)")
                params.extend([[t], [t]])
        if appearance and platform == Platform.IOS:
            conds.append("ios_metadata->'appearance_support' @> %s")
            params.append(Jsonb([appearance]))
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM design_styles "
            f"WHERE {where} ORDER BY id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        items = [_to_style_summary(r) for r in rows]
        return {
            "items": items,
            "total_count": self._total(rows) or len(items),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_style(self, style_id: str) -> dict[str, Any] | None:
        row = self._one(
            "SELECT ds.*, sf.name_en AS __family_name FROM design_styles ds "
            "LEFT JOIN style_families sf ON sf.id = ds.family_id "
            "WHERE ds.id = %s LIMIT 1",
            [style_id],
        )
        if not row:
            return None
        row["style_families"] = {"name_en": row.get("__family_name") or ""}
        return _to_style_full(row)

    def list_style_facets(self, platform: Platform) -> dict[str, Any]:
        rows = self._all(
            "SELECT family_id, visual_signatures, emotional_keywords, tokens, ios_metadata "
            "FROM design_styles WHERE platform::text = %s",
            [platform.value],
        )
        families: Counter[str] = Counter(r["family_id"] for r in rows if r.get("family_id"))
        tones: Counter[str] = Counter()
        densities: Counter[str] = Counter()
        appearances: Counter[str] = Counter()
        tags: Counter[str] = Counter()
        for r in rows:
            for kw in r.get("emotional_keywords") or []:
                tones[kw] += 1
            for sig in r.get("visual_signatures") or []:
                tags[sig] += 1
            if platform == Platform.IOS:
                ios = r.get("ios_metadata") or {}
                d = ios.get("density_typical")
                if d:
                    densities[d] += 1
                for app in ios.get("appearance_support") or []:
                    appearances[app] += 1
            else:
                d = ((r.get("tokens") or {}).get("layout") or {}).get("density")
                if d:
                    densities[d] += 1
        return {
            "families": [{"value": v, "count": c} for v, c in families.most_common()],
            "tones": [{"value": v, "count": c} for v, c in tones.most_common()],
            "densities": [{"value": v, "count": c} for v, c in densities.most_common()],
            "appearances": [{"value": v, "count": c} for v, c in appearances.most_common()],
            "tag_vocabulary": [{"value": v, "count": c} for v, c in tags.most_common()],
            "platform": platform.value,
        }

    # -------------------------------------------------------------------------
    # Palettes
    # -------------------------------------------------------------------------

    def list_palettes(
        self, platform: Platform, *,
        family: str | None = None, appearance: str | None = None,
        mood: str | None = None, tags: list[str] | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["platform::text = %s"]
        params: list[Any] = [platform.value]
        if family:
            conds.append("family_id = %s")
            params.append(family)
        if mood:
            conds.append("tags @> %s")
            params.append([mood])
        if tags:
            for t in tags:
                conds.append("tags @> %s")
                params.append([t])
        if appearance:
            conds.append("tags @> %s")
            params.append([appearance])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM color_palettes "
            f"WHERE {where} ORDER BY id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        items = [_to_palette_summary(r) for r in rows]
        return {
            "items": items,
            "total_count": self._total(rows) or len(items),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_palette(self, palette_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM color_palettes WHERE id = %s LIMIT 1", [palette_id])
        return _to_palette_full(row) if row else None

    def list_palette_facets(self, platform: Platform) -> dict[str, Any]:
        rows = self._all(
            "SELECT family_id, tags, dark_mode_first FROM color_palettes WHERE platform::text = %s",
            [platform.value],
        )
        families: Counter[str] = Counter()
        moods: Counter[str] = Counter()
        appearances: Counter[str] = Counter()
        bg_modes: Counter[str] = Counter()
        for r in rows:
            if r.get("family_id"):
                families[r["family_id"]] += 1
            for t in r.get("tags") or []:
                if t in {"warm", "cool", "neutral", "mixed"}:
                    moods[t] += 1
                if t in {"light", "dark"}:
                    appearances[t] += 1
            if r.get("dark_mode_first") and "dark" not in {a for a in appearances}:
                appearances["dark"] += 1
        return {
            "families": [{"value": v, "count": c} for v, c in families.most_common()],
            "moods": [{"value": v, "count": c} for v, c in moods.most_common()],
            "appearances": [{"value": v, "count": c} for v, c in appearances.most_common()],
            "background_modes": [{"value": v, "count": c} for v, c in bg_modes.most_common()],
            "platform": platform.value,
        }

    # -------------------------------------------------------------------------
    # Font pairs
    # -------------------------------------------------------------------------

    def list_font_pairs(
        self, platform: Platform, *,
        category_id: str | None = None, style_fit: list[str] | None = None,
        tags: list[str] | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["platform::text = %s"]
        params: list[Any] = [platform.value]
        if category_id:
            conds.append("category_id = %s")
            params.append(category_id)
        if style_fit:
            for sid in style_fit:
                conds.append("style_fit @> %s")
                params.append([sid])
        if tags:
            for t in tags:
                conds.append("mood @> %s")
                params.append([t])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM font_pairs "
            f"WHERE {where} ORDER BY id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_font_pair_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_font_pair(self, font_pair_id: str) -> dict[str, Any] | None:
        row = self._one(
            "SELECT fp.*, fpc.name_en AS __category_name FROM font_pairs fp "
            "LEFT JOIN font_pair_categories fpc ON fpc.id = fp.category_id "
            "WHERE fp.id = %s LIMIT 1",
            [font_pair_id],
        )
        if not row:
            return None
        row["font_pair_categories"] = {"name_en": row.get("__category_name") or ""}
        return _to_font_pair_full(row)

    def list_font_pair_facets(self, platform: Platform) -> dict[str, Any]:
        rows = self._all(
            "SELECT category_id, mood FROM font_pairs WHERE platform::text = %s",
            [platform.value],
        )
        cats: Counter[str] = Counter(r["category_id"] for r in rows if r.get("category_id"))
        tags: Counter[str] = Counter()
        for r in rows:
            for m in r.get("mood") or []:
                tags[m] += 1
        return {
            "categories": [{"value": v, "count": c} for v, c in cats.most_common()],
            "tags": [{"value": v, "count": c} for v, c in tags.most_common()],
            "platform": platform.value,
        }

    # -------------------------------------------------------------------------
    # Domains
    # -------------------------------------------------------------------------

    def list_domains(
        self, *, category_id: str | None = None, audience: str | None = None,
        tone: str | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["TRUE"]
        params: list[Any] = []
        if category_id:
            conds.append("category_id = %s")
            params.append(category_id)
        if audience:
            conds.append("audience = %s")
            params.append(audience)
        if tone:
            conds.append("tone @> %s")
            params.append([tone])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM domains "
            f"WHERE {where} ORDER BY id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_domain_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_domain(
        self, domain_id: str, platform: Platform, top_n: int = 5,
    ) -> dict[str, Any] | None:
        row = self._one(
            "SELECT d.*, dc.name_en AS __category_name FROM domains d "
            "LEFT JOIN domain_categories dc ON dc.id = d.category_id "
            "WHERE d.id = %s LIMIT 1",
            [domain_id],
        )
        if not row:
            return None
        row["domain_categories"] = {"name_en": row.get("__category_name") or ""}
        domain = _to_domain_full(row)
        from designlib_mcp.services.cross_links import recommendations_for_domain
        domain["recommendations"] = recommendations_for_domain(self, domain_id, platform, top_n=top_n)
        return domain

    def list_domain_facets(self) -> dict[str, Any]:
        rows = self._all(
            "SELECT category_id, audience, tone, data_density, ui_patterns FROM domains"
        )
        cats: Counter[str] = Counter(r["category_id"] for r in rows if r.get("category_id"))
        audiences: Counter[str] = Counter(r["audience"] for r in rows if r.get("audience"))
        tones: Counter[str] = Counter()
        densities: Counter[str] = Counter(r["data_density"] for r in rows if r.get("data_density"))
        patterns: Counter[str] = Counter()
        for r in rows:
            for t in r.get("tone") or []:
                tones[t] += 1
            for p in r.get("ui_patterns") or []:
                patterns[p] += 1
        return {
            "categories": [{"value": v, "count": c} for v, c in cats.most_common()],
            "audiences": [{"value": v, "count": c} for v, c in audiences.most_common()],
            "tones": [{"value": v, "count": c} for v, c in tones.most_common()],
            "data_densities": [{"value": v, "count": c} for v, c in densities.most_common()],
            "ui_patterns": [{"value": v, "count": c} for v, c in patterns.most_common()],
        }

    # -------------------------------------------------------------------------
    # Cross-link helpers
    # -------------------------------------------------------------------------

    def palettes_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT * FROM color_palettes WHERE style_fit @> %s LIMIT %s",
            [[style_id], limit],
        )
        return [_to_palette_summary(r) for r in rows]

    def font_pairs_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT * FROM font_pairs WHERE style_fit @> %s LIMIT %s",
            [[style_id], limit],
        )
        return [_to_font_pair_summary(r) for r in rows]

    def style_domain_scores(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT key_b, score FROM recommendation_scores "
            "WHERE matrix_type = 'style_domain' AND key_a = %s "
            "ORDER BY score DESC LIMIT %s",
            [style_id, limit],
        )
        if not rows:
            return []
        domain_ids = [r["key_b"] for r in rows]
        domains = self._all(
            "SELECT id, name_en, category_id FROM domains WHERE id = ANY(%s)",
            [domain_ids],
        )
        by_id = {d["id"]: d for d in domains}
        out = []
        for r in rows:
            d = by_id.get(r["key_b"])
            if d:
                out.append({
                    "domain_id": d["id"],
                    "name": d.get("name_en") or d["id"],
                    "category_id": d.get("category_id") or "",
                    "score": float(r["score"]),
                })
        return out

    def domain_top_styles(
        self, domain_id: str, platform: Platform, limit: int,
    ) -> list[dict[str, Any]]:
        rows = self._all(
            "SELECT key_a, score FROM recommendation_scores "
            "WHERE matrix_type = 'style_domain' AND key_b = %s "
            "ORDER BY score DESC LIMIT %s",
            [domain_id, limit * 2],
        )
        if not rows:
            return []
        style_ids = [r["key_a"] for r in rows]
        styles = self._all(
            "SELECT * FROM design_styles WHERE id = ANY(%s) AND platform::text = %s",
            [style_ids, platform.value],
        )
        by_id = {s["id"]: s for s in styles}
        out = []
        for r in rows:
            s = by_id.get(r["key_a"])
            if s:
                out.append({**_to_style_summary(s), "score": float(r["score"])})
            if len(out) >= limit:
                break
        return out

    # -------------------------------------------------------------------------
    # Chart types
    # -------------------------------------------------------------------------

    def list_chart_types(
        self, *, data_type: str | None = None, a11y_grade: str | None = None,
        library: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["TRUE"]
        params: list[Any] = []
        if data_type:
            conds.append("data_type = %s")
            params.append(data_type)
        if a11y_grade:
            conds.append("a11y_grade = %s")
            params.append(a11y_grade)
        if library:
            conds.append("library_recommendation @> %s")
            params.append([library])
        if keyword:
            conds.append("keywords @> %s")
            params.append([keyword.strip().lower()])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM chart_types "
            f"WHERE {where} ORDER BY sort_order, id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_chart_type_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_chart_type(self, chart_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM chart_types WHERE id = %s LIMIT 1", [chart_id])
        return _to_chart_type_full(row) if row else None

    def list_chart_type_facets(self) -> dict[str, Any]:
        rows = self._all(
            "SELECT data_type, a11y_grade, library_recommendation, interactive_level FROM chart_types"
        )
        data_types: Counter[str] = Counter()
        grades: Counter[str] = Counter()
        libs: Counter[str] = Counter()
        levels: Counter[str] = Counter()
        for r in rows:
            if r.get("data_type"):
                data_types[r["data_type"]] += 1
            if r.get("a11y_grade"):
                grades[r["a11y_grade"]] += 1
            for lib in r.get("library_recommendation") or []:
                libs[lib] += 1
            if r.get("interactive_level"):
                levels[r["interactive_level"]] += 1
        return {
            "data_types": [{"value": v, "count": c} for v, c in data_types.most_common()],
            "a11y_grades": [{"value": v, "count": c} for v, c in grades.most_common()],
            "libraries": [{"value": v, "count": c} for v, c in libs.most_common()],
            "interactive_levels": [{"value": v, "count": c} for v, c in levels.most_common()],
        }

    # -------------------------------------------------------------------------
    # Landing patterns
    # -------------------------------------------------------------------------

    def list_landing_patterns(
        self, *, keyword: str | None = None, cta_placement: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["TRUE"]
        params: list[Any] = []
        if cta_placement:
            conds.append("primary_cta_placement = %s")
            params.append(cta_placement)
        if keyword:
            conds.append("keywords @> %s")
            params.append([keyword.strip().lower()])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM landing_patterns "
            f"WHERE {where} ORDER BY sort_order, id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_landing_pattern_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_landing_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM landing_patterns WHERE id = %s LIMIT 1", [pattern_id])
        return _to_landing_pattern_full(row) if row else None

    def list_landing_pattern_facets(self) -> dict[str, Any]:
        rows = self._all("SELECT primary_cta_placement FROM landing_patterns")
        ctas: Counter[str] = Counter(
            r["primary_cta_placement"] for r in rows if r.get("primary_cta_placement")
        )
        return {
            "cta_placements": [{"value": v, "count": c} for v, c in ctas.most_common()],
        }

    # -------------------------------------------------------------------------
    # Icons
    # -------------------------------------------------------------------------

    def list_icons(
        self, *, category: str | None = None, library: str | None = None,
        style: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["TRUE"]
        params: list[Any] = []
        if category:
            conds.append("category = %s")
            params.append(category)
        if library:
            conds.append("library_name = %s")
            params.append(library)
        if style:
            conds.append("style = %s")
            params.append(style)
        if keyword:
            conds.append("keywords @> %s")
            params.append([keyword.strip().lower()])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM icons "
            f"WHERE {where} ORDER BY sort_order, id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_icon_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_icon(self, icon_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM icons WHERE id = %s LIMIT 1", [icon_id])
        return _to_icon_full(row) if row else None

    def list_icon_facets(self) -> dict[str, Any]:
        rows = self._all("SELECT category, library_name, style FROM icons")
        cats: Counter[str] = Counter(r["category"] for r in rows if r.get("category"))
        libs: Counter[str] = Counter(r["library_name"] for r in rows if r.get("library_name"))
        styles: Counter[str] = Counter(r["style"] for r in rows if r.get("style"))
        return {
            "categories": [{"value": v, "count": c} for v, c in cats.most_common()],
            "libraries": [{"value": v, "count": c} for v, c in libs.most_common()],
            "styles": [{"value": v, "count": c} for v, c in styles.most_common()],
        }

    # -------------------------------------------------------------------------
    # Inspiration pages
    # -------------------------------------------------------------------------

    def list_inspiration_pages(
        self, *, page_type: str | None = None, appearance: str | None = None,
        style_family: str | None = None, industry: str | None = None,
        density: str | None = None, mood: str | None = None,
        keyword: str | None = None, signature: str | None = None,
        good_for_product_type: str | None = None, good_for_stage: str | None = None,
        limit: int = 25, offset: int = 0,
    ) -> dict[str, Any]:
        cols = (
            "id, page_type, appearance, style_family, industry, mood, keywords, "
            "screenshot_path, description, use_when"
        )
        conds = ["TRUE"]
        params: list[Any] = []
        if page_type:
            conds.append("page_type = %s")
            params.append(page_type)
        if appearance:
            conds.append("appearance = %s")
            params.append(appearance)
        if style_family:
            conds.append("style_family = %s")
            params.append(style_family)
        if industry:
            conds.append("industry = %s")
            params.append(industry)
        if density:
            conds.append("density = %s")
            params.append(density)
        if mood:
            conds.append("mood @> %s")
            params.append([mood])
        if signature:
            conds.append("visual_signatures @> %s")
            params.append([signature])
        if good_for_product_type:
            conds.append("good_for_product_types @> %s")
            params.append([good_for_product_type])
        if good_for_stage:
            conds.append("good_for_stages @> %s")
            params.append([good_for_stage])
        if keyword:
            conds.append("keywords @> %s")
            params.append([keyword.strip().lower()])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT {cols}, count(*) OVER() AS total_count FROM inspiration_pages "
            f"WHERE {where} ORDER BY id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_inspiration_page_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_inspiration_page(self, page_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM inspiration_pages WHERE id = %s LIMIT 1", [page_id])
        return _to_inspiration_page_full(row) if row else None

    def list_inspiration_page_facets(self) -> dict[str, Any]:
        rows = self._all(
            "SELECT page_type, appearance, density, style_family, industry, mood, "
            "visual_signatures, good_for_product_types, good_for_stages FROM inspiration_pages"
        )
        page_types: Counter[str] = Counter()
        appearances: Counter[str] = Counter()
        densities: Counter[str] = Counter()
        families: Counter[str] = Counter()
        industries: Counter[str] = Counter()
        moods: Counter[str] = Counter()
        sigs: Counter[str] = Counter()
        gfpt: Counter[str] = Counter()
        gfs: Counter[str] = Counter()
        for r in rows:
            if r.get("page_type"):
                page_types[r["page_type"]] += 1
            if r.get("appearance"):
                appearances[r["appearance"]] += 1
            if r.get("density"):
                densities[r["density"]] += 1
            if r.get("style_family"):
                families[r["style_family"]] += 1
            if r.get("industry"):
                industries[r["industry"]] += 1
            for m in r.get("mood") or []:
                moods[m] += 1
            for s in r.get("visual_signatures") or []:
                sigs[s] += 1
            for x in r.get("good_for_product_types") or []:
                gfpt[x] += 1
            for x in r.get("good_for_stages") or []:
                gfs[x] += 1
        return {
            "page_types": [{"value": v, "count": c} for v, c in page_types.most_common()],
            "appearances": [{"value": v, "count": c} for v, c in appearances.most_common()],
            "densities": [{"value": v, "count": c} for v, c in densities.most_common()],
            "style_families": [{"value": v, "count": c} for v, c in families.most_common(50)],
            "industries": [{"value": v, "count": c} for v, c in industries.most_common(50)],
            "moods": [{"value": v, "count": c} for v, c in moods.most_common()],
            "visual_signatures": [{"value": v, "count": c} for v, c in sigs.most_common()],
            "good_for_product_types": [{"value": v, "count": c} for v, c in gfpt.most_common()],
            "good_for_stages": [{"value": v, "count": c} for v, c in gfs.most_common()],
        }

    # -------------------------------------------------------------------------
    # Animations
    # -------------------------------------------------------------------------

    def list_animations(
        self, *,
        category: str | None = None,
        framework: str | None = None,
        interactivity: str | None = None,
        complexity: str | None = None,
        style_tag: str | None = None,
        placement: str | None = None,
        use_when: str | None = None,
        library: str | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        conds = ["TRUE"]
        params: list[Any] = []
        if category:
            conds.append("category = %s")
            params.append(category)
        if framework:
            conds.append("framework = %s")
            params.append(framework)
        if interactivity:
            conds.append("interactivity = %s")
            params.append(interactivity)
        if complexity:
            conds.append("complexity = %s")
            params.append(complexity)
        if style_tag:
            conds.append("style_tags @> %s")
            params.append([style_tag.strip().lower()])
        if placement:
            conds.append("placement @> %s")
            params.append([placement.strip().lower()])
        if use_when:
            conds.append("use_when @> %s")
            params.append([use_when.strip().lower()])
        if library:
            conds.append("libraries @> %s")
            params.append([library.strip().lower()])
        if keyword:
            conds.append("keyword @> %s")
            params.append([keyword.strip().lower()])
        where = " AND ".join(conds)
        rows = self._all(
            f"SELECT *, count(*) OVER() AS total_count FROM animations "
            f"WHERE {where} ORDER BY sort_order, id LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return {
            "items": [_to_animation_summary(r) for r in rows],
            "total_count": self._total(rows) or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_animation(self, animation_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM animations WHERE id = %s LIMIT 1", [animation_id])
        return _to_animation_full(row) if row else None

    def list_animation_facets(self) -> dict[str, Any]:
        rows = self._all(
            "SELECT category, framework, interactivity, complexity, "
            "libraries, style_tags, placement, use_when FROM animations"
        )
        cats: Counter[str] = Counter()
        fws: Counter[str] = Counter()
        libs: Counter[str] = Counter()
        inters: Counter[str] = Counter()
        comps: Counter[str] = Counter()
        styles: Counter[str] = Counter()
        places: Counter[str] = Counter()
        whens: Counter[str] = Counter()
        for r in rows:
            if r.get("category"):
                cats[r["category"]] += 1
            if r.get("framework"):
                fws[r["framework"]] += 1
            if r.get("interactivity"):
                inters[r["interactivity"]] += 1
            if r.get("complexity"):
                comps[r["complexity"]] += 1
            for v in r.get("libraries") or []:
                libs[v] += 1
            for v in r.get("style_tags") or []:
                styles[v] += 1
            for v in r.get("placement") or []:
                places[v] += 1
            for v in r.get("use_when") or []:
                whens[v] += 1

        def _agg(c: Counter[str]) -> list[dict]:
            return [{"value": v, "count": n} for v, n in c.most_common()]

        return {
            "categories": _agg(cats),
            "frameworks": _agg(fws),
            "libraries": _agg(libs),
            "interactivity": _agg(inters),
            "complexity": _agg(comps),
            "style_tags": _agg(styles),
            "placement": _agg(places),
            "use_when": _agg(whens),
        }
