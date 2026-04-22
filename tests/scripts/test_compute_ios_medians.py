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
