from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.repository.base import CatalogRepository


def list_social_templates_handler(
    repo: CatalogRepository, *,
    format: str | None = None,
    category: str | None = None,
    aspect_ratio: str | None = None,
    appearance: str | None = None,
    platform: str | None = None,
    style_tag: str | None = None,
    use_when: str | None = None,
    industry: str | None = None,
    keyword: str | None = None,
    slides: int | None = None,
    limit: int = 25, offset: int = 0,
) -> dict[str, Any]:
    raw = repo.list_social_templates(
        format=format, category=category,
        aspect_ratio=aspect_ratio, appearance=appearance,
        platform=platform, style_tag=style_tag,
        use_when=use_when, industry=industry,
        keyword=keyword, slides=slides,
        limit=limit, offset=offset,
    )
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "social_template_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_social_template_handler(
    repo: CatalogRepository, *, template_id: str, include_html: bool = True,
) -> dict[str, Any]:
    template = repo.get_social_template(template_id, include_html=include_html)
    if template is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Social template '{template_id}' not found.",
            "field": "template_id",
            "suggest_tool": "list_social_templates",
        }
    template["meta"] = {
        "schema_version": "1.0", "platform": None,
        "entity_type": "social_template", "truncated": False,
    }
    return enforce_character_limit(template, limit=CHARACTER_LIMIT)


def list_social_template_facets_handler(repo: CatalogRepository) -> dict[str, Any]:
    raw = repo.list_social_template_facets()
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "social_template_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(
        name="list_social_templates",
        description=(
            "List social media design templates for stories and carousels "
            "(Instagram-style, fillable HTML/CSS with content slots). Filter by "
            "format (story|carousel), category (promo, educational, listicle, "
            "quote, ...), aspect_ratio (9:16|4:5|1:1), appearance (light|dark|mixed), "
            "platform (social network: instagram|tiktok|linkedin|facebook), "
            "style_tag, situation (use_when), industry, keyword, or slides "
            "(desired slide count; matches templates whose min-max range covers it)."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_social_templates(
        format: str | None = None,
        category: str | None = None,
        aspect_ratio: str | None = None,
        appearance: str | None = None,
        platform: str | None = None,
        style_tag: str | None = None,
        use_when: str | None = None,
        industry: str | None = None,
        keyword: str | None = None,
        slides: int | None = None,
        limit: int = 25, offset: int = 0,
    ) -> dict[str, Any]:
        return list_social_templates_handler(
            repo, format=format, category=category,
            aspect_ratio=aspect_ratio, appearance=appearance,
            platform=platform, style_tag=style_tag,
            use_when=use_when, industry=industry,
            keyword=keyword, slides=slides,
            limit=limit, offset=offset,
        )

    @mcp.tool(
        name="get_social_template",
        description=(
            "Get a social template by id: full spec (slides with fillable slots and "
            "per-slot max_chars, fonts, content brief) plus the self-contained HTML/CSS "
            "template with {{slot}} placeholders and :root design tokens for re-skinning. "
            "Pass include_html=false to browse the spec without the HTML payload "
            "(html_chars reports its size)."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def get_social_template(
        template_id: str, include_html: bool = True,
    ) -> dict[str, Any]:
        return get_social_template_handler(
            repo, template_id=template_id, include_html=include_html,
        )

    @mcp.tool(
        name="list_social_template_facets",
        description=(
            "Facet counts for social templates: formats, categories, aspect_ratios, "
            "appearances, platforms (social networks), style_tags, use_when, "
            "industries. Use to discover valid filter values for list_social_templates."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_social_template_facets() -> dict[str, Any]:
        return list_social_template_facets_handler(repo)
