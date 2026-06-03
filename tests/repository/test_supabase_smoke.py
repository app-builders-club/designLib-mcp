import pytest
from designlib_mcp.repository.postgres_repo import PostgresRepository


@pytest.mark.integration
def test_health_check(settings):
    repo = PostgresRepository.from_settings(settings)
    assert repo.health_check() is True
