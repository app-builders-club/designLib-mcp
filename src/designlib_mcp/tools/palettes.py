from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.models.common import Platform
from designlib_mcp.repository.base import CatalogRepository


def list_palettes_handler(
    repo: CatalogRepository, *,
    platform: str, family: str | None = None, appearance: str | None = None,
    mood: str | None = None, tags: list[str] | None = None,
    limit: int = 50, offset: int = 0,
) -> dict[str, Any]:
    p = Platform(platform)
    raw = repo.list_palettes(p, family=family, appearance=appearance,
                             mood=mood, tags=tags, limit=limit, offset=offset)
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": platform,
            "entity_type": "palette_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_palette_handler(repo: CatalogRepository, *, palette_id: str) -> dict[str, Any]:
    pal = repo.get_palette(palette_id)
    if pal is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Palette '{palette_id}' not found.",
            "field": "palette_id",
            "suggest_tool": "list_palettes",
        }
    pal["meta"] = {
        "schema_version": "1.0", "platform": pal.get("platform"),
        "entity_type": "palette", "truncated": False,
    }
    return enforce_character_limit(pal, limit=CHARACTER_LIMIT)


def list_palette_facets_handler(repo: CatalogRepository, *, platform: str) -> dict[str, Any]:
    p = Platform(platform)
    raw = repo.list_palette_facets(p)
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": platform,
            "entity_type": "palette_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(name="list_palettes",
              description="List color palettes filtered by platform and optional facets.",
              annotations={"readOnlyHint": True, "destructiveHint": False,
                           "idempotentHint": True, "openWorldHint": True})
    def list_palettes(platform: str, family: str | None = None,
                      appearance: str | None = None, mood: str | None = None,
                      tags: list[str] | None = None, limit: int = 50,
                      offset: int = 0) -> dict[str, Any]:
        return list_palettes_handler(repo, platform=platform, family=family,
                                     appearance=appearance, mood=mood, tags=tags,
                                     limit=limit, offset=offset)

    @mcp.tool(name="get_palette", description="Get a single color palette with full role mapping.",
              annotations={"readOnlyHint": True, "destructiveHint": False,
                           "idempotentHint": True, "openWorldHint": True})
    def get_palette(palette_id: str) -> dict[str, Any]:
        return get_palette_handler(repo, palette_id=palette_id)

    @mcp.tool(name="list_palette_facets",
              description="List available facet values for the palettes catalog.",
              annotations={"readOnlyHint": True, "destructiveHint": False,
                           "idempotentHint": True, "openWorldHint": True})
    def list_palette_facets(platform: str) -> dict[str, Any]:
        return list_palette_facets_handler(repo, platform=platform)
