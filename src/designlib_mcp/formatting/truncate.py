from __future__ import annotations
import json
from typing import Any


def _serialized_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False))


def enforce_character_limit(payload: dict, *, limit: int) -> dict:
    """If serialized payload exceeds `limit` characters, drop tail items and set truncated=True.

    For non-list payloads, just sets meta.truncated=True without modification — caller is
    responsible for using stricter filters.
    """
    if _serialized_size(payload) <= limit:
        return payload
    items = payload.get("items")
    if not isinstance(items, list):
        meta = payload.setdefault("meta", {})
        meta["truncated"] = True
        return payload
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = {**payload, "items": items[:mid]}
        if _serialized_size(candidate) <= limit:
            lo = mid
        else:
            hi = mid - 1
    truncated_items = items[:lo]
    out = {**payload, "items": truncated_items}
    out.setdefault("meta", {})["truncated"] = True
    return out
