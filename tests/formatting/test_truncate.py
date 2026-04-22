from designlib_mcp.formatting.truncate import enforce_character_limit


def test_no_truncation_when_small():
    payload = {"items": [{"x": 1}, {"x": 2}], "meta": {"truncated": False}}
    out = enforce_character_limit(payload, limit=10_000)
    assert out["meta"]["truncated"] is False
    assert len(out["items"]) == 2


def test_truncates_items_when_over_limit():
    big_item = {"k": "x" * 1_000}
    payload = {"items": [big_item] * 30, "meta": {"truncated": False}}
    out = enforce_character_limit(payload, limit=5_000)
    assert out["meta"]["truncated"] is True
    assert len(out["items"]) < 30


def test_skips_when_no_items_field():
    payload = {"id": "x", "meta": {"truncated": False}}
    out = enforce_character_limit(payload, limit=10)
    assert out["meta"]["truncated"] is True
