from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.repository.base import CatalogRepository


def list_icons_handler(
    repo: CatalogRepository, *,
    category: str | None = None, library: str | None = None,
    style: str | None = None, keyword: str | None = None,
    limit: int = 50, offset: int = 0,
) -> dict[str, Any]:
    raw = repo.list_icons(
        category=category, library=library, style=style,
        keyword=keyword, limit=limit, offset=offset,
    )
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "icon_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_icon_handler(repo: CatalogRepository, *, icon_id: str) -> dict[str, Any]:
    icon = repo.get_icon(icon_id)
    if icon is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Icon '{icon_id}' not found.",
            "field": "icon_id",
            "suggest_tool": "list_icons",
        }
    icon["meta"] = {
        "schema_version": "1.0", "platform": None,
        "entity_type": "icon", "truncated": False,
    }
    return enforce_character_limit(icon, limit=CHARACTER_LIMIT)


def list_icon_facets_handler(repo: CatalogRepository) -> dict[str, Any]:
    raw = repo.list_icon_facets()
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "icon_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(
        name="list_icons",
        description="List icons from supported libraries filtered by category, library, style or keyword.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_icons(
        category: str | None = None, library: str | None = None,
        style: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        return list_icons_handler(
            repo, category=category, library=library, style=style,
            keyword=keyword, limit=limit, offset=offset,
        )

    @mcp.tool(
        name="get_icon",
        description="Get a single icon with import code and usage example.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def get_icon(icon_id: str) -> dict[str, Any]:
        return get_icon_handler(repo, icon_id=icon_id)

    @mcp.tool(
        name="list_icon_facets",
        description="List available facet values for the icons catalog.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_icon_facets() -> dict[str, Any]:
        return list_icon_facets_handler(repo)
