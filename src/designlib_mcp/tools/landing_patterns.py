from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.repository.base import CatalogRepository


def list_landing_patterns_handler(
    repo: CatalogRepository, *,
    keyword: str | None = None, cta_placement: str | None = None,
    limit: int = 50, offset: int = 0,
) -> dict[str, Any]:
    raw = repo.list_landing_patterns(
        keyword=keyword, cta_placement=cta_placement, limit=limit, offset=offset,
    )
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "landing_pattern_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_landing_pattern_handler(repo: CatalogRepository, *, pattern_id: str) -> dict[str, Any]:
    pattern = repo.get_landing_pattern(pattern_id)
    if pattern is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Landing pattern '{pattern_id}' not found.",
            "field": "pattern_id",
            "suggest_tool": "list_landing_patterns",
        }
    pattern["meta"] = {
        "schema_version": "1.0", "platform": None,
        "entity_type": "landing_pattern", "truncated": False,
    }
    return enforce_character_limit(pattern, limit=CHARACTER_LIMIT)


def list_landing_pattern_facets_handler(repo: CatalogRepository) -> dict[str, Any]:
    raw = repo.list_landing_pattern_facets()
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "landing_pattern_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(
        name="list_landing_patterns",
        description="List landing page patterns with section order and CTA placement guidance.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_landing_patterns(
        keyword: str | None = None, cta_placement: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        return list_landing_patterns_handler(
            repo, keyword=keyword, cta_placement=cta_placement,
            limit=limit, offset=offset,
        )

    @mcp.tool(
        name="get_landing_pattern",
        description="Get a single landing pattern with section order, color and conversion guidance.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def get_landing_pattern(pattern_id: str) -> dict[str, Any]:
        return get_landing_pattern_handler(repo, pattern_id=pattern_id)

    @mcp.tool(
        name="list_landing_pattern_facets",
        description="List available facet values for the landing patterns catalog.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_landing_pattern_facets() -> dict[str, Any]:
        return list_landing_pattern_facets_handler(repo)
