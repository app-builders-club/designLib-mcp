import pytest
from designlib_mcp.repository.supabase_repo import SupabaseRepository


@pytest.mark.integration
def test_health_check(settings):
    repo = SupabaseRepository.from_settings(settings)
    assert repo.health_check() is True
