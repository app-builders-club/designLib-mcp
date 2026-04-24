from __future__ import annotations
from typing import Any, Protocol, runtime_checkable

from designlib_mcp.models.common import Platform


@runtime_checkable
class CatalogRepository(Protocol):
    # Styles
    def list_styles(
        self, platform: Platform, *,
        family: str | None = None, appearance: str | None = None,
        tone: str | None = None, density: str | None = None,
        tags: list[str] | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_style(self, style_id: str) -> dict[str, Any] | None: ...

    def list_style_facets(self, platform: Platform) -> dict[str, Any]: ...

    # Palettes
    def list_palettes(
        self, platform: Platform, *,
        family: str | None = None, appearance: str | None = None,
        mood: str | None = None, tags: list[str] | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_palette(self, palette_id: str) -> dict[str, Any] | None: ...

    def list_palette_facets(self, platform: Platform) -> dict[str, Any]: ...

    # Font pairs
    def list_font_pairs(
        self, platform: Platform, *,
        category_id: str | None = None, style_fit: list[str] | None = None,
        tags: list[str] | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_font_pair(self, font_pair_id: str) -> dict[str, Any] | None: ...

    def list_font_pair_facets(self, platform: Platform) -> dict[str, Any]: ...

    # Domains
    def list_domains(
        self, *, category_id: str | None = None, audience: str | None = None,
        tone: str | None = None, limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_domain(
        self, domain_id: str, platform: Platform, top_n: int = 5,
    ) -> dict[str, Any] | None: ...

    def list_domain_facets(self) -> dict[str, Any]: ...

    # Cross-link helpers used by services/cross_links.py
    def palettes_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]: ...
    def font_pairs_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]: ...
    def style_domain_scores(self, style_id: str, limit: int) -> list[dict[str, Any]]: ...
    def domain_top_styles(self, domain_id: str, platform: Platform, limit: int) -> list[dict[str, Any]]: ...

    # Chart types
    def list_chart_types(
        self, *, data_type: str | None = None, a11y_grade: str | None = None,
        library: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_chart_type(self, chart_id: str) -> dict[str, Any] | None: ...

    def list_chart_type_facets(self) -> dict[str, Any]: ...

    # Landing patterns
    def list_landing_patterns(
        self, *, keyword: str | None = None, cta_placement: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_landing_pattern(self, pattern_id: str) -> dict[str, Any] | None: ...

    def list_landing_pattern_facets(self) -> dict[str, Any]: ...

    # Icons
    def list_icons(
        self, *, category: str | None = None, library: str | None = None,
        style: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]: ...

    def get_icon(self, icon_id: str) -> dict[str, Any] | None: ...

    def list_icon_facets(self) -> dict[str, Any]: ...
