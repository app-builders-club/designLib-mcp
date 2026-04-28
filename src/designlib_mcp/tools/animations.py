from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.repository.base import CatalogRepository


def list_animations_handler(
    repo: CatalogRepository, *,
    category: str | None = None,
    framework: str | None = None,
    interactivity: str | None = None,
    complexity: str | None = None,
    style_tag: str | None = None,
    placement: str | None = None,
    use_when: str | None = None,
    library: str | None = None,
    keyword: str | None = None,
    limit: int = 50, offset: int = 0,
) -> dict[str, Any]:
    raw = repo.list_animations(
        category=category, framework=framework,
        interactivity=interactivity, complexity=complexity,
        style_tag=style_tag, placement=placement,
        use_when=use_when, library=library, keyword=keyword,
        limit=limit, offset=offset,
    )
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "animation_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_animation_handler(repo: CatalogRepository, *, animation_id: str) -> dict[str, Any]:
    animation = repo.get_animation(animation_id)
    if animation is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Animation '{animation_id}' not found.",
            "field": "animation_id",
            "suggest_tool": "list_animations",
        }
    animation["meta"] = {
        "schema_version": "1.0", "platform": None,
        "entity_type": "animation", "truncated": False,
    }
    return enforce_character_limit(animation, limit=CHARACTER_LIMIT)


def list_animation_facets_handler(repo: CatalogRepository) -> dict[str, Any]:
    raw = repo.list_animation_facets()
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "animation_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(
        name="list_animations",
        description=(
            "List animated UI building blocks (backgrounds, hero sections, loaders, "
            "text effects, cursor effects, decorations). Filter by category, framework, "
            "library, complexity, style, placement, situation (use_when), or keyword."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_animations(
        category: str | None = None,
        framework: str | None = None,
        interactivity: str | None = None,
        complexity: str | None = None,
        style_tag: str | None = None,
        placement: str | None = None,
        use_when: str | None = None,
        library: str | None = None,
        keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        return list_animations_handler(
            repo, category=category, framework=framework,
            interactivity=interactivity, complexity=complexity,
            style_tag=style_tag, placement=placement,
            use_when=use_when, library=library, keyword=keyword,
            limit=limit, offset=offset,
        )

    @mcp.tool(
        name="get_animation",
        description=(
            "Get a single animation by id. Returns the standardized prompt_text "
            "an agent can paste into the user's project."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def get_animation(animation_id: str) -> dict[str, Any]:
        return get_animation_handler(repo, animation_id=animation_id)

    @mcp.tool(
        name="list_animation_facets",
        description="List available facet values for the animations catalog.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_animation_facets() -> dict[str, Any]:
        return list_animation_facets_handler(repo)
