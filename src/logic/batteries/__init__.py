"""Battery scorers for modular baseline assessment."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
BATTERY_DIR = ROOT / "data/processed/batteries"


def _as_float(value, default=None):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=1)
def load_registry() -> dict:
    path = BATTERY_DIR / "registry.json"
    if not path.exists():
        return {"version": "v1", "order": ["fms"], "default_selected": ["fms"], "batteries": []}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def load_battery_spec(battery_id: str) -> dict:
    path = BATTERY_DIR / f"{battery_id}.json"
    if not path.exists():
        return {"id": battery_id}
    return json.loads(path.read_text(encoding="utf-8"))


def _band(seconds: Optional[float], red_max: float, yellow_max: float) -> str:
    if seconds is None:
        return "unscored"
    if seconds <= red_max:
        return "red"
    if seconds <= yellow_max:
        return "yellow"
    return "green"


def score_breathing(data: dict, spec: Optional[dict] = None) -> dict:
    spec = spec or load_battery_spec("breathing")
    bands = spec.get("bands") or {}
    bolt_cfg = bands.get("bolt") or {"red_max": 34, "yellow_max": 60}
    tlc_cfg = bands.get("tlc") or {"red_max": 44, "yellow_max": 90}
    bolt = _as_float(data.get("bolt_seconds"))
    tlc = _as_float(data.get("tlc_seconds"))
    bolt_band = _band(bolt, bolt_cfg["red_max"], bolt_cfg["yellow_max"])
    tlc_band = _band(tlc, tlc_cfg["red_max"], tlc_cfg["yellow_max"])
    findings = []
    recommendations = []
    for label, band, seconds in (("BOLT", bolt_band, bolt), ("TLC", tlc_band, tlc)):
        if band == "red":
            findings.append(f"{label} hold {seconds:g}s is red — limited respiratory control / CO2 tolerance.")
            recommendations.append("Prioritize nasal breathing drills and submaximal aerobic base before hard conditioning.")
        elif band == "yellow":
            findings.append(f"{label} hold {seconds:g}s is yellow — room to improve breath control.")
        elif band == "green":
            findings.append(f"{label} hold {seconds:g}s is green.")
    worst = "green"
    for b in (bolt_band, tlc_band):
        if b == "red":
            worst = "red"
            break
        if b == "yellow" and worst != "red":
            worst = "yellow"
        if b == "unscored" and worst == "green":
            worst = "unscored"
    return {
        "battery": "breathing",
        "bolt_seconds": bolt,
        "tlc_seconds": tlc,
        "bolt_band": bolt_band,
        "tlc_band": tlc_band,
        "band": worst,
        "findings": findings,
        "recommendations": recommendations,
        "comment": data.get("comment") or "",
        "needs_hints": ["breathing"] if worst == "red" else ([] if worst != "yellow" else ["breathing"]),
    }


def score_beighton(data: dict, age: Optional[int] = None, spec: Optional[dict] = None) -> dict:
    spec = spec or load_battery_spec("beighton")
    points = spec.get("points") or []
    scored = []
    total = 0
    for point in points:
        key = point["key"]
        on = bool(_as_int(data.get(key), 0) > 0 or data.get(key) is True)
        scored.append({"key": key, "label": point.get("label", key), "positive": on})
        if on:
            total += 1
    youth = age is not None and age < 18
    threshold = (
        spec.get("hypermobility_threshold_youth", 5)
        if youth
        else spec.get("hypermobility_threshold_adult", 4)
    )
    hypermobile = total >= threshold
    findings = [f"Beighton score {total}/9."]
    recommendations = []
    needs = []
    if hypermobile:
        findings.append(f"Hypermobility flagged (threshold ≥{threshold}).")
        recommendations.append("Bias toward stability and motor control before aggressive end-range mobility.")
        needs.extend(["mobility", "stability"])
    return {
        "battery": "beighton",
        "total": total,
        "max": 9,
        "hypermobile": hypermobile,
        "threshold": threshold,
        "points": scored,
        "findings": findings,
        "recommendations": recommendations,
        "needs_hints": needs,
    }


def score_mcgill(data: dict, spec: Optional[dict] = None) -> dict:
    spec = spec or load_battery_spec("mcgill")
    ratios_cfg = spec.get("ratios") or {}
    flex = _as_float(data.get("flexor_seconds"))
    lat_r = _as_float(data.get("lateral_right_seconds"))
    lat_l = _as_float(data.get("lateral_left_seconds"))
    ext = _as_float(data.get("extensor_seconds"))

    ratios = {}
    flags = []
    findings = []
    recommendations = []
    needs = []

    if flex is not None and ext and ext > 0:
        ratios["flexion_extension"] = round(flex / ext, 3)
        if ratios["flexion_extension"] >= ratios_cfg.get("flexion_extension_max", 1.0):
            flags.append("flexion_extension_high")
            findings.append(f"Flexion:Extension ratio {ratios['flexion_extension']} (≥1.0) — extensor endurance lag.")
            recommendations.append("Emphasize trunk extensor endurance and anti-flexion control.")
            needs.append("stability")

    if lat_r is not None and lat_l is not None and max(lat_r, lat_l) > 0:
        lo, hi = min(lat_r, lat_l), max(lat_r, lat_l)
        ratios["bridge_right_left"] = round(lat_r / lat_l, 3) if lat_l else None
        sym_min = ratios_cfg.get("bridge_symmetry_min", 0.95)
        sym_max = ratios_cfg.get("bridge_symmetry_max", 1.05)
        if ratios["bridge_right_left"] is not None and not (sym_min <= ratios["bridge_right_left"] <= sym_max):
            flags.append("lateral_asymmetry")
            findings.append(f"Lateral bridge asymmetry R:L = {ratios['bridge_right_left']}.")
            needs.append("asymmetry")
            needs.append("stability")

    side_max = ratios_cfg.get("side_extension_max", 0.75)
    for side, val in (("right", lat_r), ("left", lat_l)):
        if val is not None and ext and ext > 0:
            key = f"{side}_bridge_extension"
            ratios[key] = round(val / ext, 3)
            if ratios[key] >= side_max:
                flags.append(f"{side}_bridge_extension_high")
                findings.append(f"{side.title()} bridge:extension {ratios[key]} (≥{side_max}).")
                needs.append("stability")

    if not findings and any(v is not None for v in (flex, lat_r, lat_l, ext)):
        findings.append("McGill ratios within expected ranges.")

    return {
        "battery": "mcgill",
        "flexor_seconds": flex,
        "lateral_right_seconds": lat_r,
        "lateral_left_seconds": lat_l,
        "extensor_seconds": ext,
        "ratios": ratios,
        "flags": flags,
        "findings": findings,
        "recommendations": recommendations,
        "comment": data.get("comment") or "",
        "needs_hints": sorted(set(needs)),
    }


def score_bunkie(data: dict, spec: Optional[dict] = None) -> dict:
    spec = spec or load_battery_spec("bunkie")
    lines_spec = spec.get("lines") or []
    asym_thresh = spec.get("asymmetry_threshold_seconds", 8)
    lines_out = []
    findings = []
    recommendations = []
    needs = []
    weak_count = 0

    for line in lines_spec:
        key = line["key"]
        row = data.get(key) if isinstance(data.get(key), dict) else {}
        left = _as_float(row.get("left") if row else data.get(f"{key}_left"))
        right = _as_float(row.get("right") if row else data.get(f"{key}_right"))
        comment = (row.get("comment") if row else None) or data.get(f"{key}_comment") or ""
        norm_min = line.get("norm_min", 30)
        left_ok = left is None or left >= norm_min
        right_ok = right is None or right >= norm_min
        asym = None
        if left is not None and right is not None:
            asym = abs(left - right)
        weak = (left is not None and not left_ok) or (right is not None and not right_ok)
        asymmetric = asym is not None and asym >= asym_thresh
        if weak:
            weak_count += 1
            findings.append(
                f"{line['label']}: below normative floor ({norm_min}s) "
                f"(L={left if left is not None else '—'} R={right if right is not None else '—'})."
            )
            recommendations.append(f"Address {line.get('sling', key)} endurance and control.")
            needs.append("stability")
        if asymmetric:
            findings.append(f"{line['label']}: L/R asymmetry {asym:g}s.")
            needs.append("asymmetry")
        lines_out.append(
            {
                "key": key,
                "label": line["label"],
                "sling": line.get("sling"),
                "left": left,
                "right": right,
                "comment": comment,
                "norm_min": norm_min,
                "left_ok": left_ok,
                "right_ok": right_ok,
                "asymmetry_seconds": asym,
                "weak": weak,
                "asymmetric": asymmetric,
            }
        )

    if not findings:
        findings.append("Bunkie holds meet normative floors without meaningful asymmetry.")

    return {
        "battery": "bunkie",
        "lines": lines_out,
        "weak_line_count": weak_count,
        "findings": findings,
        "recommendations": recommendations,
        "needs_hints": sorted(set(needs)),
    }


def score_muscular_endurance(
    data: dict,
    gender: Optional[str] = None,
    spec: Optional[dict] = None,
) -> dict:
    spec = spec or load_battery_spec("muscular_endurance")
    tests_spec = spec.get("tests") or []
    thresholds = spec.get("low_thresholds") or {}
    sex = (gender or "male").lower()
    if sex not in ("male", "female"):
        sex = "male"
    results = []
    findings = []
    recommendations = []
    needs = []

    for test in tests_spec:
        key = test["key"]
        thr = (thresholds.get(key) or {}).get(sex)
        raw = data.get(key)
        if test.get("sides"):
            left = right = None
            if isinstance(raw, dict):
                left = _as_float(raw.get("left"))
                right = _as_float(raw.get("right"))
            else:
                left = _as_float(data.get(f"{key}_left"))
                right = _as_float(data.get(f"{key}_right"))
            low = False
            if thr is not None:
                for side_val in (left, right):
                    if side_val is not None and side_val < thr:
                        low = True
            if low:
                findings.append(f"{test['label']}: below endurance floor (L={left} R={right}, floor {thr}).")
                needs.append("endurance")
                recommendations.append(f"Build {test['label'].lower()} capacity with progressive volume.")
            results.append(
                {"key": key, "label": test["label"], "left": left, "right": right, "low": low, "threshold": thr}
            )
        else:
            reps = None
            if isinstance(raw, dict):
                reps = _as_float(raw.get("reps") or raw.get("score"))
            else:
                reps = _as_float(raw)
            low = thr is not None and reps is not None and reps < thr
            if low:
                findings.append(f"{test['label']}: {reps:g} reps below floor ({thr}).")
                needs.append("endurance")
                recommendations.append(f"Progress {test['label'].lower()} density.")
            elif reps is not None:
                findings.append(f"{test['label']}: {reps:g} reps.")
            results.append({"key": key, "label": test["label"], "reps": reps, "low": low, "threshold": thr})

    return {
        "battery": "muscular_endurance",
        "tests": results,
        "findings": findings,
        "recommendations": recommendations,
        "comment": data.get("comment") or "",
        "needs_hints": sorted(set(needs)),
    }


SCORERS = {
    "breathing": score_breathing,
    "beighton": score_beighton,
    "mcgill": score_mcgill,
    "bunkie": score_bunkie,
    "muscular_endurance": score_muscular_endurance,
}
