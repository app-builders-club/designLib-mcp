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


from collections import Counter
from statistics import median

CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.0}


def _mode(values: list) -> str | None:
    cleaned = [v for v in values if v]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def aggregate_typography(apps: list[dict]) -> dict:
    body = [a.get("typography", {}).get("body") for a in apps]
    heading = [a.get("typography", {}).get("heading") for a in apps]
    return {
        "body_classification": _mode(body),
        "heading_classification": _mode(heading),
        "mono_present": any(a.get("typography", {}).get("mono_present") for a in apps),
        "tabular_numerics_present": any(
            a.get("typography", {}).get("tabular_numerics_present") for a in apps
        ),
    }


def aggregate_layout(apps: list[dict]) -> dict:
    densities = [a.get("layout", {}).get("density_typical") for a in apps]
    list_styles = [a.get("layout", {}).get("list_style_dominant") for a in apps]
    radii = [
        a.get("layout", {}).get("corner_radius_cards_pt_median")
        for a in apps
        if a.get("layout", {}).get("corner_radius_cards_pt_median") is not None
    ]
    return {
        "density_typical": _mode(densities),
        "list_style_dominant": _mode(list_styles),
        "corner_radius_cards_pt_median": median(radii) if radii else None,
    }


def aggregate_liquid_glass(apps: list[dict]) -> dict:
    postures = [a.get("liquid_glass", {}).get("posture") for a in apps]
    surface_counts: Counter[str] = Counter()
    n_apps = len(apps)
    for a in apps:
        for s in a.get("liquid_glass", {}).get("surfaces_affected_union", []):
            surface_counts[s] += 1
    threshold = 0.70 * n_apps
    surfaces = sorted(s for s, c in surface_counts.items() if c >= threshold)
    return {"posture": _mode(postures) or "unclear", "surfaces_affected": surfaces}


def aggregate_iconography(apps: list[dict]) -> str | None:
    return _mode([a.get("iconography", {}).get("icon_system") for a in apps])


def top_reference_apps(apps: list[dict], top_n: int) -> list[str]:
    def score(app: dict) -> float:
        weight = CONFIDENCE_WEIGHT.get(app.get("_confidence", "low"), 0.0)
        return float(app.get("screenshot_count", 0)) * weight
    ranked = sorted(apps, key=score, reverse=True)
    return [a["slug"] for a in ranked[:top_n]]


import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTION_DIR = REPO_ROOT / "extraction"
DATA_DIR = REPO_ROOT / "data"


def _confidence_for_family_aggregation(c: str) -> bool:
    # Include all confidence levels so every family produces output.
    # Low-confidence usage is recorded via review_flags (see compute_family_medians).
    return c in {"high", "medium", "low"}


def compute_family_medians(
    apps_by_slug: dict[str, dict],
    family_assignments: list[dict],
) -> dict[str, dict]:
    families: dict[str, list[dict]] = {}
    for row in family_assignments:
        if not _confidence_for_family_aggregation(row.get("confidence", "low")):
            continue
        slug = row["slug"]
        family = row["family_assigned"]
        app = apps_by_slug.get(slug)
        if not app:
            continue
        app = {**app, "_confidence": row["confidence"]}
        families.setdefault(family, []).append(app)

    out: dict[str, dict] = {}
    for family, apps in families.items():
        n = len(apps)
        low_count = sum(1 for a in apps if a.get("_confidence") == "low")
        flags: list[str] = []
        if n < 3:
            flags.append(f"app_count_below_3 ({n})")
        if low_count > 0:
            flags.append(f"uses_low_confidence_apps ({low_count}/{n})")
        out[family] = {
            "app_count": n,
            "palette_light": aggregate_palette(apps, mode="light"),
            "palette_dark": aggregate_palette(apps, mode="dark"),
            "typography": aggregate_typography(apps),
            "layout": aggregate_layout(apps),
            "liquid_glass": aggregate_liquid_glass(apps),
            "iconography": aggregate_iconography(apps),
            "reference_apps": top_reference_apps(apps, top_n=5),
            "review_flags": flags,
        }
    return out


def _load_apps_by_slug(extraction_dir: Path) -> dict[str, dict]:
    aggregated_dir = extraction_dir / "aggregated"
    out: dict[str, dict] = {}
    for f in aggregated_dir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        out[data["slug"]] = data
    return out


def _load_family_assignments(extraction_dir: Path) -> list[dict]:
    raw = json.loads((extraction_dir / "family_assignments.json").read_text(encoding="utf-8"))
    return raw["assignments"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extraction-dir", default=str(EXTRACTION_DIR))
    parser.add_argument("--out", default=str(DATA_DIR / "ios_family_medians.json"))
    args = parser.parse_args()

    extraction_dir = Path(args.extraction_dir)
    out_path = Path(args.out)
    if not extraction_dir.exists():
        print(f"extraction dir not found: {extraction_dir}", file=sys.stderr)
        return 1

    apps_by_slug = _load_apps_by_slug(extraction_dir)
    family_assignments = _load_family_assignments(extraction_dir)
    medians = compute_family_medians(apps_by_slug, family_assignments)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(medians, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] wrote {len(medians)} families -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
