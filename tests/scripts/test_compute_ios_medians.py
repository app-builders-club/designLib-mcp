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


from scripts.compute_ios_medians import (
    aggregate_typography, aggregate_layout, aggregate_liquid_glass,
    aggregate_iconography, top_reference_apps,
)


def test_aggregate_typography_majority_vote():
    apps = _load_apps()
    typo = aggregate_typography(apps)
    assert typo["body_classification"] == "sf_pro_text"
    assert typo["heading_classification"] == "sf_pro_display"


def test_aggregate_layout_uses_mode_and_median():
    apps = _load_apps()
    layout = aggregate_layout(apps)
    assert layout["density_typical"] == "comfortable"
    assert layout["list_style_dominant"] == "plain"
    assert layout["corner_radius_cards_pt_median"] == 18.0


def test_aggregate_liquid_glass_keeps_70_percent_surfaces():
    apps = _load_apps()
    lg = aggregate_liquid_glass(apps)
    assert lg["posture"] == "native_fit"
    assert "tab_bar" in lg["surfaces_affected"]
    assert "toolbar" not in lg["surfaces_affected"]


def test_aggregate_iconography_mode():
    apps = _load_apps()
    icon = aggregate_iconography(apps)
    assert icon == "custom_glyph_set"


def test_top_reference_apps_weights_confidence():
    apps = _load_apps()
    refs = top_reference_apps(apps, top_n=3)
    assert refs == ["gamma", "alpha", "beta"]


from scripts.compute_ios_medians import compute_family_medians


def test_compute_family_medians_smoke(tmp_path):
    apps = _load_apps()
    family_assignments = [
        {"slug": "alpha", "family_assigned": "demo_family", "confidence": "high"},
        {"slug": "beta",  "family_assigned": "demo_family", "confidence": "medium"},
        {"slug": "gamma", "family_assigned": "demo_family", "confidence": "high"},
    ]
    out = compute_family_medians(apps_by_slug={a["slug"]: a for a in apps},
                                 family_assignments=family_assignments)
    assert "demo_family" in out
    fam = out["demo_family"]
    assert fam["app_count"] == 3
    assert fam["palette_light"]["background"].startswith("#")
    assert fam["palette_dark"] is None
    assert fam["typography"]["heading_classification"] == "sf_pro_display"
    assert fam["layout"]["density_typical"] == "comfortable"
    assert fam["liquid_glass"]["posture"] == "native_fit"
    assert fam["reference_apps"] == ["gamma", "alpha", "beta"]
    assert fam["review_flags"] == []
