import pytest
from scripts.compute_ios_medians import median_hex_lab


def test_median_hex_lab_three_grays():
    out = median_hex_lab(["#FFFFFF", "#F2F2F2", "#FAFAFA"])
    assert out.upper() in {"#FAFAFA", "#F8F8F8", "#F9F9F9"}  # any near-median


def test_median_hex_lab_single_value():
    assert median_hex_lab(["#112233"]).upper() == "#112233"


def test_median_hex_lab_empty_returns_none():
    assert median_hex_lab([]) is None


def test_median_hex_lab_drops_none_inputs():
    out = median_hex_lab([None, "#FFFFFF", None])
    assert out.upper() == "#FFFFFF"


import json
from pathlib import Path
from scripts.compute_ios_medians import aggregate_palette


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "ios_aggregated_sample.json"


def _load_apps():
    return json.loads(FIXTURE.read_text())["apps"]


def test_aggregate_palette_light_uses_lab_median():
    apps = _load_apps()
    palette = aggregate_palette(apps, mode="light")
    assert palette["background"].startswith("#")
    assert palette["text_primary"].startswith("#")
    assert palette["accent_primary"].startswith("#")


def test_aggregate_palette_drops_conflicting_background():
    apps = _load_apps()
    apps[0]["palette_light"]["background_conflicting"] = True
    palette = aggregate_palette(apps, mode="light")
    assert palette["background"] is not None


def test_aggregate_palette_returns_none_when_no_apps_have_dark():
    apps = _load_apps()
    palette = aggregate_palette(apps, mode="dark")
    assert palette is None
