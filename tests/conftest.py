import os
import pytest
from dotenv import load_dotenv
from designlib_mcp.config import Settings


def _env_present() -> bool:
    load_dotenv()
    return bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_ANON_KEY"))


@pytest.fixture(scope="session")
def settings() -> Settings:
    if not _env_present():
        pytest.skip("Supabase env not configured; set SUPABASE_URL and SUPABASE_ANON_KEY")
    return Settings.from_env()
