from __future__ import annotations
from typing import Any
from supabase import create_client, Client

from designlib_mcp.config import Settings
from designlib_mcp.models.common import Platform


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

    # All concrete methods are added in Phase G (Tasks 21–24).
    def list_styles(self, platform: Platform, **_: Any) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 21")

    def get_style(self, style_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("Implemented in Task 21")

    def list_style_facets(self, platform: Platform) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 21")

    def list_palettes(self, platform: Platform, **_: Any) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 22")

    def get_palette(self, palette_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("Implemented in Task 22")

    def list_palette_facets(self, platform: Platform) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 22")

    def list_font_pairs(self, platform: Platform, **_: Any) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 23")

    def get_font_pair(self, font_pair_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("Implemented in Task 23")

    def list_font_pair_facets(self, platform: Platform) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 23")

    def list_domains(self, **_: Any) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 24")

    def get_domain(self, domain_id: str, platform: Platform, top_n: int = 5) -> dict[str, Any] | None:
        raise NotImplementedError("Implemented in Task 24")

    def list_domain_facets(self) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Task 24")

    def palettes_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError("Implemented in Task 25")

    def font_pairs_used_by_style(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError("Implemented in Task 25")

    def style_domain_scores(self, style_id: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError("Implemented in Task 25")

    def domain_top_styles(self, domain_id: str, platform: Platform, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError("Implemented in Task 25")
