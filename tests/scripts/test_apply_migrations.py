from pathlib import Path
from scripts.apply_migrations import discover_migrations


def test_discover_migrations_returns_sorted(tmp_path: Path):
    (tmp_path / "002_b.sql").write_text("-- b")
    (tmp_path / "001_a.sql").write_text("-- a")
    (tmp_path / "003_c.sql").write_text("-- c")
    files = discover_migrations(tmp_path)
    assert [p.name for p in files] == ["001_a.sql", "002_b.sql", "003_c.sql"]


def test_discover_migrations_skips_non_sql(tmp_path: Path):
    (tmp_path / "001_a.sql").write_text("-- a")
    (tmp_path / "README.md").write_text("readme")
    files = discover_migrations(tmp_path)
    assert [p.name for p in files] == ["001_a.sql"]
