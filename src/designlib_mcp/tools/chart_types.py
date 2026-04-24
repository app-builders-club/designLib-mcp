from __future__ import annotations
from typing import Any

from designlib_mcp.config import CHARACTER_LIMIT
from designlib_mcp.formatting.truncate import enforce_character_limit
from designlib_mcp.repository.base import CatalogRepository


def list_chart_types_handler(
    repo: CatalogRepository, *,
    data_type: str | None = None, a11y_grade: str | None = None,
    library: str | None = None, keyword: str | None = None,
    limit: int = 50, offset: int = 0,
) -> dict[str, Any]:
    raw = repo.list_chart_types(
        data_type=data_type, a11y_grade=a11y_grade, library=library,
        keyword=keyword, limit=limit, offset=offset,
    )
    payload = {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "chart_type_list", "truncated": False,
        },
    }
    return enforce_character_limit(payload, limit=CHARACTER_LIMIT)


def get_chart_type_handler(repo: CatalogRepository, *, chart_id: str) -> dict[str, Any]:
    chart = repo.get_chart_type(chart_id)
    if chart is None:
        return {
            "error_code": "NOT_FOUND",
            "message": f"Chart type '{chart_id}' not found.",
            "field": "chart_id",
            "suggest_tool": "list_chart_types",
        }
    chart["meta"] = {
        "schema_version": "1.0", "platform": None,
        "entity_type": "chart_type", "truncated": False,
    }
    return enforce_character_limit(chart, limit=CHARACTER_LIMIT)


def list_chart_type_facets_handler(repo: CatalogRepository) -> dict[str, Any]:
    raw = repo.list_chart_type_facets()
    return {
        **raw,
        "meta": {
            "schema_version": "1.0", "platform": None,
            "entity_type": "chart_type_facets", "truncated": False,
        },
    }


def register(mcp, repo: CatalogRepository) -> None:
    @mcp.tool(
        name="list_chart_types",
        description="List chart types with accessibility guidance and library recommendations.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_chart_types(
        data_type: str | None = None, a11y_grade: str | None = None,
        library: str | None = None, keyword: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> dict[str, Any]:
        return list_chart_types_handler(
            repo, data_type=data_type, a11y_grade=a11y_grade,
            library=library, keyword=keyword, limit=limit, offset=offset,
        )

    @mcp.tool(
        name="get_chart_type",
        description="Get a single chart type with when-to-use, accessibility and library guidance.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def get_chart_type(chart_id: str) -> dict[str, Any]:
        return get_chart_type_handler(repo, chart_id=chart_id)

    @mcp.tool(
        name="list_chart_type_facets",
        description="List available facet values for the chart types catalog.",
        annotations={"readOnlyHint": True, "destructiveHint": False,
                     "idempotentHint": True, "openWorldHint": True},
    )
    def list_chart_type_facets() -> dict[str, Any]:
        return list_chart_type_facets_handler(repo)
