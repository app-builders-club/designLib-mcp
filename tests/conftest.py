import os
import pytest
from dotenv import load_dotenv
from designlib_mcp.config import Settings


def _env_present() -> bool:
    load_dotenv()
    return bool(os.getenv("DATABASE_URL"))


@pytest.fixture(scope="session")
def settings() -> Settings:
    if not _env_present():
        pytest.skip("DATABASE_URL not configured; set it to a reachable Postgres")
    return Settings.from_env()
