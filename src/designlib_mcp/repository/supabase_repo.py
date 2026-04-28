from __future__ import annotations
from collections import Counter
from typing import Any
from supabase import create_client, Client

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
)


class SupabaseRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseRepository":
        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        return cls(client)

    def health_check(self) -> bool:
        # Cheap read against a known table to confirm connectivity.
        # style_families is small (≤24 rows) and present after migrations.
        resp = self._client.table("style_families").select("id").limit(1).execute()
        return isinstance(resp.data, list)

    # -------------------------------------------------------------------------
    # Styles
    # -------------------------------------------------------------------------

    def list_styles(
        self, platform: Platform, *,
        family: str | None = None, appearance: str | None = None,
        tone: str | None = None, density: str | None = None,
        tags: list[str] | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        q = self._client.table("design_styles").select("*", count="exact").eq("platform", platform.value)
        if family:
            q = q.eq("family_id", family)
        if tone:
            q = q.contains("emotional_keywords", [tone])
        if density:
            if platform == Platform.IOS:
                q = q.eq("ios_metadata->>density_typical", density)
            else:
                q = q.eq("tokens->'layout'->>'density'", density)
        if tags:
            for t in tags:
                q = q.or_(f"visual_signatures.cs.{{{t}}},emotional_keywords.cs.{{{t}}}")
        if appearance and platform == Platform.IOS:
            q = q.contains("ios_metadata->appearance_support", [appearance])
        q = q.range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        items = [_to_style_summary(r) for r in rows]
        return {
            "items": items,
            "total_count": resp.count or len(items),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_style(self, style_id: str) -> dict[str, Any] | None:
        resp = self._client.table("design_styles").select("*, style_families(name_en)") \
            .eq("id", style_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_style_full(rows[0])

    def list_style_facets(self, platform: Platform) -> dict[str, Any]:
        resp = self._client.table("design_styles") \
            .select("family_id, visual_signatures, emotional_keywords, tokens, ios_metadata") \
            .eq("platform", platform.value).execute()
        rows = resp.data or []
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
        q = self._client.table("color_palettes").select("*", count="exact").eq("platform", platform.value)
        if family:
            q = q.eq("family_id", family)
        if mood:
            q = q.contains("tags", [mood])
        if tags:
            for t in tags:
                q = q.contains("tags", [t])
        if appearance:
            q = q.contains("tags", [appearance])
        q = q.range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        items = [_to_palette_summary(r) for r in rows]
        return {
            "items": items,
            "total_count": resp.count or len(items),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_palette(self, palette_id: str) -> dict[str, Any] | None:
        resp = self._client.table("color_palettes").select("*").eq("id", palette_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_palette_full(rows[0])

    def list_palette_facets(self, platform: Platform) -> dict[str, Any]:
        resp = self._client.table("color_palettes") \
            .select("family_id, tags, dark_mode_first").eq("platform", platform.value).execute()
        rows = resp.data or []
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
        q = self._client.table("font_pairs").select("*", count="exact").eq("platform", platform.value)
        if category_id:
            q = q.eq("category_id", category_id)
        if style_fit:
            for sid in style_fit:
                q = q.contains("style_fit", [sid])
        if tags:
            for t in tags:
                q = q.contains("mood", [t])
        q = q.range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_font_pair_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
            "platform": platform.value,
        }

    def get_font_pair(self, font_pair_id: str) -> dict[str, Any] | None:
        resp = self._client.table("font_pairs").select("*, font_pair_categories(name_en)") \
            .eq("id", font_pair_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_font_pair_full(rows[0])

    def list_font_pair_facets(self, platform: Platform) -> dict[str, Any]:
        resp = self._client.table("font_pairs") \
            .select("category_id, mood").eq("platform", platform.value).execute()
        rows = resp.data or []
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
        q = self._client.table("domains").select("*", count="exact")
        if category_id:
            q = q.eq("category_id", category_id)
        if audience:
            q = q.eq("audience", audience)
        if tone:
            q = q.contains("tone", [tone])
        q = q.range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_domain_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_domain(
        self, domain_id: str, platform: Platform, top_n: int = 5,
    ) -> dict[str, Any] | None:
        resp = self._client.table("domains").select("*, domain_categories(name_en)") \
            .eq("id", domain_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        domain = _to_domain_full(rows[0])
        from designlib_mcp.services.cross_links import recommendations_for_domain
        domain["recommendations"] = recommendations_for_domain(self, domain_id, platform, top_n=top_n)
        return domain

    def list_domain_facets(self) -> dict[str, Any]:
        resp = self._client.table("domains") \
            .select("category_id, audience, tone, data_density, ui_patterns").execute()
        rows = resp.data or []
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
        resp = self._client.table("color_palettes").select("*") \
            .contains("style_fit", [style_id]).limit(limit).execute()
        return [_to_palette_summary(r) for r in (resp.data or [])]

    def font_pairs_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        resp = self._client.table("font_pairs").select("*") \
            .contains("style_fit", [style_id]).limit(limit).execute()
        return [_to_font_pair_summary(r) for r in (resp.data or [])]

    def style_domain_scores(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        resp = self._client.table("recommendation_scores").select("key_b, score") \
            .eq("matrix_type", "style_domain").eq("key_a", style_id) \
            .order("score", desc=True).limit(limit).execute()
        rows = resp.data or []
        if not rows:
            return []
        domain_ids = [r["key_b"] for r in rows]
        domains = self._client.table("domains").select("id, name_en, category_id") \
            .in_("id", domain_ids).execute()
        by_id = {d["id"]: d for d in (domains.data or [])}
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
        resp = self._client.table("recommendation_scores").select("key_a, score") \
            .eq("matrix_type", "style_domain").eq("key_b", domain_id) \
            .order("score", desc=True).limit(limit * 2).execute()
        rows = resp.data or []
        if not rows:
            return []
        style_ids = [r["key_a"] for r in rows]
        styles = self._client.table("design_styles").select("*") \
            .in_("id", style_ids).eq("platform", platform.value).execute()
        by_id = {s["id"]: s for s in (styles.data or [])}
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
        q = self._client.table("chart_types").select("*", count="exact")
        if data_type:
            q = q.eq("data_type", data_type)
        if a11y_grade:
            q = q.eq("a11y_grade", a11y_grade)
        if library:
            q = q.contains("library_recommendation", [library])
        if keyword:
            q = q.contains("keywords", [keyword.strip().lower()])
        q = q.order("sort_order").range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_chart_type_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_chart_type(self, chart_id: str) -> dict[str, Any] | None:
        resp = self._client.table("chart_types").select("*").eq("id", chart_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_chart_type_full(rows[0])

    def list_chart_type_facets(self) -> dict[str, Any]:
        resp = self._client.table("chart_types").select(
            "data_type, a11y_grade, library_recommendation, interactive_level"
        ).execute()
        rows = resp.data or []
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
        q = self._client.table("landing_patterns").select("*", count="exact")
        if cta_placement:
            q = q.eq("primary_cta_placement", cta_placement)
        if keyword:
            q = q.contains("keywords", [keyword.strip().lower()])
        q = q.order("sort_order").range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_landing_pattern_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_landing_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        resp = self._client.table("landing_patterns").select("*").eq("id", pattern_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_landing_pattern_full(rows[0])

    def list_landing_pattern_facets(self) -> dict[str, Any]:
        resp = self._client.table("landing_patterns").select("primary_cta_placement").execute()
        rows = resp.data or []
        ctas: Counter[str] = Counter(r["primary_cta_placement"] for r in rows if r.get("primary_cta_placement"))
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
        q = self._client.table("icons").select("*", count="exact")
        if category:
            q = q.eq("category", category)
        if library:
            q = q.eq("library_name", library)
        if style:
            q = q.eq("style", style)
        if keyword:
            q = q.contains("keywords", [keyword.strip().lower()])
        q = q.order("sort_order").range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_icon_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_icon(self, icon_id: str) -> dict[str, Any] | None:
        resp = self._client.table("icons").select("*").eq("id", icon_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_icon_full(rows[0])

    def list_icon_facets(self) -> dict[str, Any]:
        resp = self._client.table("icons").select("category, library_name, style").execute()
        rows = resp.data or []
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
        q = self._client.table("inspiration_pages").select(cols, count="exact")
        if page_type:
            q = q.eq("page_type", page_type)
        if appearance:
            q = q.eq("appearance", appearance)
        if style_family:
            q = q.eq("style_family", style_family)
        if industry:
            q = q.eq("industry", industry)
        if density:
            q = q.eq("density", density)
        if mood:
            q = q.contains("mood", [mood])
        if signature:
            q = q.contains("visual_signatures", [signature])
        if good_for_product_type:
            q = q.contains("good_for_product_types", [good_for_product_type])
        if good_for_stage:
            q = q.contains("good_for_stages", [good_for_stage])
        if keyword:
            q = q.contains("keywords", [keyword.strip().lower()])
        q = q.order("id").range(offset, offset + limit - 1)
        resp = q.execute()
        rows = resp.data or []
        return {
            "items": [_to_inspiration_page_summary(r) for r in rows],
            "total_count": resp.count or len(rows),
            "limit": limit,
            "offset": offset,
        }

    def get_inspiration_page(self, page_id: str) -> dict[str, Any] | None:
        resp = self._client.table("inspiration_pages").select("*").eq("id", page_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return None
        return _to_inspiration_page_full(rows[0])

    def list_inspiration_page_facets(self) -> dict[str, Any]:
        resp = self._client.table("inspiration_pages").select(
            "page_type, appearance, density, style_family, industry, mood, "
            "visual_signatures, good_for_product_types, good_for_stages"
        ).execute()
        rows = resp.data or []
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
