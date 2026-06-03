from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

CHARACTER_LIMIT: int = 25_000


@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL is required")
        return cls(database_url=dsn)
