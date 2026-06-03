import pytest
from designlib_mcp.config import Settings, CHARACTER_LIMIT


def test_character_limit_constant():
    assert CHARACTER_LIMIT == 25_000


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:pw@localhost:5432/postgres")
    s = Settings.from_env()
    assert s.database_url == "postgresql://postgres:pw@localhost:5432/postgres"


def test_settings_missing_required_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Prevent load_dotenv from repopulating DATABASE_URL from a local .env
    monkeypatch.setattr("designlib_mcp.config.load_dotenv", lambda: None)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        Settings.from_env()
