import json
from pathlib import Path

import pytest

from scripts.emit_social_templates_sql import (
    load_staging, row_to_sql, validate_record,
)

FIXTURE = Path(__file__).parent / "fixtures" / "social_template_staging_sample.json"


def _rec() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_load_staging_reads_all_json(tmp_path: Path):
    (tmp_path / "a.json").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "b.json").write_text(
        FIXTURE.read_text(encoding="utf-8").replace("test_sample", "test_sample_b"),
        encoding="utf-8",
    )
    rows = load_staging(tmp_path)
    assert len(rows) == 2
    ids = {r["id"] for r in rows}
    assert ids == {"social_story_test_sample", "social_story_test_sample_b"}


def test_validate_record_accepts_valid():
    validate_record(_rec())


def test_validate_record_rejects_missing_required():
    rec = _rec()
    rec.pop("content_brief")
    with pytest.raises(ValueError, match="content_brief"):
        validate_record(rec)


def test_validate_record_rejects_unknown_field():
    rec = _rec()
    rec["typo_field"] = "x"
    with pytest.raises(ValueError, match="typo_field"):
        validate_record(rec)


def test_validate_record_rejects_bad_enum():
    rec = _rec()
    rec["category"] = "not_a_category"
    with pytest.raises(ValueError, match="category"):
        validate_record(rec)


def test_validate_record_rejects_story_with_wrong_ratio():
    rec = _rec()
    rec["aspect_ratio"] = "1:1"
    with pytest.raises(ValueError, match="9:16"):
        validate_record(rec)


def test_validate_record_rejects_bad_platform():
    rec = _rec()
    rec["platform_fit"] = ["instagram", "myspace"]
    with pytest.raises(ValueError, match="myspace"):
        validate_record(rec)


def test_validate_record_rejects_uppercase_tags():
    rec = _rec()
    rec["style_tags"] = ["Bold_Type"]
    with pytest.raises(ValueError, match="lowercased"):
        validate_record(rec)


def test_validate_record_rejects_slide_count_mismatch():
    rec = _rec()
    rec["slide_count"] = 3
    with pytest.raises(ValueError, match="slide_count"):
        validate_record(rec)


def test_validate_record_rejects_slot_html_mismatch():
    rec = _rec()
    rec["html_template"] = rec["html_template"].replace("{{point_body}}", "{{wrong_token}}")
    with pytest.raises(ValueError, match="mismatch"):
        validate_record(rec)


def test_validate_record_rejects_duplicate_slot_names():
    rec = _rec()
    rec["slides"][1]["slots"][1]["name"] = "point_title"
    with pytest.raises(ValueError, match="duplicate"):
        validate_record(rec)


def test_validate_record_rejects_variable_range_without_repeatable():
    rec = _rec()
    rec["slides"][1]["repeatable"] = False
    with pytest.raises(ValueError, match="repeatable"):
        validate_record(rec)


def test_validate_record_rejects_missing_css_token():
    rec = _rec()
    rec["html_template"] = rec["html_template"].replace("--accent-contrast", "--accent-alt")
    with pytest.raises(ValueError, match="--accent-contrast"):
        validate_record(rec)


def test_validate_record_rejects_oversized_html():
    rec = _rec()
    rec["html_template"] += "<!-- " + "x" * 25_000 + " -->"
    with pytest.raises(ValueError, match="too large"):
        validate_record(rec)


def test_validate_record_rejects_base64():
    rec = _rec()
    rec["html_template"] = rec["html_template"].replace(
        'data-slot="bg_image"', 'data-slot="bg_image" style="background:url(data:image/png;base64,AAAA)"'
    )
    with pytest.raises(ValueError, match="base64"):
        validate_record(rec)


def test_row_to_sql_shape():
    rec = _rec()
    rec["sort_order"] = 0
    sql = row_to_sql(rec)
    assert sql.startswith("INSERT INTO social_templates (")
    assert "json_populate_record(NULL::social_templates" in sql
    assert sql.rstrip().endswith("ON CONFLICT DO NOTHING;")
    assert "''" not in FIXTURE.name  # sanity: escaping tested below


def test_row_to_sql_escapes_single_quotes():
    rec = _rec()
    rec["sort_order"] = 0
    rec["title"] = "Archivo's Test"
    sql = row_to_sql(rec)
    assert "Archivo''s Test" in sql


def test_row_to_sql_upsert_variant():
    rec = _rec()
    rec["sort_order"] = 0
    sql = row_to_sql(rec, upsert=True)
    assert 'ON CONFLICT (id) DO UPDATE SET "title" = EXCLUDED."title"' in sql
    assert '"id" = EXCLUDED."id"' not in sql
