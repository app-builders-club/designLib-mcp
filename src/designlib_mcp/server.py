from __future__ import annotations
from fastmcp import FastMCP

from designlib_mcp.config import Settings
from designlib_mcp.repository.postgres_repo import PostgresRepository
from designlib_mcp.tools import (
    styles, palettes, font_pairs, domains,
    chart_types, landing_patterns, icons, inspiration_pages,
    animations,
)


def build_server() -> FastMCP:
    settings = Settings.from_env()
    repo = PostgresRepository.from_settings(settings)
    mcp = FastMCP("designlib-mcp")
    styles.register(mcp, repo)
    palettes.register(mcp, repo)
    font_pairs.register(mcp, repo)
    domains.register(mcp, repo)
    chart_types.register(mcp, repo)
    landing_patterns.register(mcp, repo)
    icons.register(mcp, repo)
    inspiration_pages.register(mcp, repo)
    animations.register(mcp, repo)
    return mcp
