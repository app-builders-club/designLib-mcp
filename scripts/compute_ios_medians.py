"""Compute median iOS family tokens from extraction/aggregated/*.json.

Phase E of designlib-mcp v1. Reads aggregated app profiles + family_assignments,
emits data/ios_family_medians.json.
"""
from __future__ import annotations
from typing import Iterable


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    # sRGB → linear
    def srgb_to_linear(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (srgb_to_linear(c) for c in rgb)
    # linear → XYZ (D65)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    # XYZ → LAB
    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _lab_to_xyz(lab: tuple[float, float, float]) -> tuple[float, float, float]:
    L, a, b = lab
    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    def finv(t: float) -> float:
        t3 = t ** 3
        return t3 if t3 > 0.008856 else (t - 16 / 116) / 7.787
    return (finv(fx) * 0.95047, finv(fy) * 1.00000, finv(fz) * 1.08883)


def _xyz_to_rgb(xyz: tuple[float, float, float]) -> tuple[int, int, int]:
    x, y, z = xyz
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b = 0.0557 * x - 0.2040 * y + 1.0570 * z
    def linear_to_srgb(v: float) -> int:
        if v <= 0:
            return 0
        if v >= 1:
            return 255
        c = 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
        return max(0, min(255, round(c * 255)))
    return (linear_to_srgb(r), linear_to_srgb(g), linear_to_srgb(b))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def median_hex_lab(hexes: Iterable[str | None]) -> str | None:
    """Return the LAB-space coordinate-wise median of input hex colors.

    None values are dropped. Returns None if no values remain.
    """
    cleaned = [h for h in hexes if h]
    if not cleaned:
        return None
    labs = [_rgb_to_lab(_hex_to_rgb(h)) for h in cleaned]
    n = len(labs)
    sorted_L = sorted(l[0] for l in labs)
    sorted_a = sorted(l[1] for l in labs)
    sorted_b = sorted(l[2] for l in labs)
    mid = n // 2
    if n % 2 == 1:
        med_lab = (sorted_L[mid], sorted_a[mid], sorted_b[mid])
    else:
        med_lab = (
            (sorted_L[mid - 1] + sorted_L[mid]) / 2,
            (sorted_a[mid - 1] + sorted_a[mid]) / 2,
            (sorted_b[mid - 1] + sorted_b[mid]) / 2,
        )
    return _rgb_to_hex(_xyz_to_rgb(_lab_to_xyz(med_lab)))


PALETTE_ROLES = (
    "background", "background_elevated", "surface_card",
    "text_primary", "text_secondary", "separator", "accent_primary",
    "semantic_destructive", "semantic_success", "semantic_warning",
)


def _palette_key(mode: str) -> str:
    return "palette_light" if mode == "light" else "palette_dark"


def _coverage_for_mode(apps: list[dict], mode: str) -> list[dict]:
    key = _palette_key(mode)
    return [a for a in apps if a.get(key)]


def aggregate_palette(apps: list[dict], mode: str) -> dict | None:
    """Aggregate per-role hex medians for a family in light or dark mode.

    Returns None when fewer than 3 apps have the requested mode (per spec rule).
    Drops a single app's `background` value when its palette has
    `background_conflicting=true`.
    """
    relevant = _coverage_for_mode(apps, mode)
    if mode == "dark" and len(relevant) < 3:
        return None
    if not relevant:
        return None

    key = _palette_key(mode)
    out: dict[str, str | None] = {}
    for role in PALETTE_ROLES:
        values: list[str | None] = []
        for app in relevant:
            pal = app.get(key) or {}
            if role == "background" and pal.get("background_conflicting"):
                continue
            values.append(pal.get(role))
        out[role] = median_hex_lab(values)
    return out
