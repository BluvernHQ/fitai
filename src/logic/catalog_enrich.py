"""Derive eligibility metadata on catalog records without inventing exercises."""

from __future__ import annotations

import re
from copy import deepcopy

HIGH_IMPACT_PATTERNS = {"plyo", "speed"}
HIGH_IMPACT_NAME = re.compile(
    r"depth jump|drop jump|box jump|broad jump|sprint|bound|hurdle hop|depth drop",
    re.I,
)
OVERHEAD = re.compile(
    r"\b(oh|overhead|snatch|jerk|military press|pike push|z press|push press|landmine press)\b",
    re.I,
)
JUMP_OR_PLY = re.compile(
    r"\b(jump|jacks|hops?|bound|plyo|depth drop|skipping|pogos?)\b",
    re.I,
)
BARBELL_SQUAT = re.compile(r"\b(bb|barbell|back squat|oh squat|overhead squat)\b", re.I)
UNILATERAL = re.compile(
    r"u/l|unilateral|single leg|\bsl\b|split|offset|suitcase|1-arm|1 arm",
    re.I,
)

LOAD_FROM_NAME = (
    (re.compile(r"deadlift|rdl|hip hinge", re.I), "deadlift"),
    (re.compile(r"bench|floor press", re.I), "bench_press"),
    (re.compile(r"\brow\b|pulldown|pull-up|chin", re.I), "row"),
    (re.compile(r"back squat|front squat|goblet|safety bar", re.I), "back_squat"),
)


def _load_basis(ex: dict) -> str | None:
    pattern = ex.get("pattern")
    name = f"{ex.get('name', '')} {ex.get('family', '')}"
    if pattern in {"core", "rotation", "gait", "warmup", "plyo", "speed", "lunge"}:
        for rx, key in LOAD_FROM_NAME:
            if rx.search(name):
                return key
        return None
    for rx, key in LOAD_FROM_NAME:
        if rx.search(name):
            return key
    if pattern == "squat":
        return "back_squat"
    if pattern == "hinge":
        return "deadlift"
    if pattern == "push":
        return "bench_press"
    if pattern == "pull":
        return "row"
    return None


def _contraindications(ex: dict, impact: str) -> list[str]:
    tags = []
    if impact == "high":
        tags.extend(["heels_lift", "pain-stop", "MOBILITY", "STABILITY", "STOP"])
    name = f"{ex.get('name', '')} {ex.get('family', '')}"
    if BARBELL_SQUAT.search(name) and ex.get("pattern") == "squat":
        tags.append("heels_lift")
    if OVERHEAD.search(name):
        tags.extend(["shoulder_mobility<=1", "arms_fall_forward", "shoulder_restriction"])
    return sorted(set(tags))


def _normalize_equipment(ex: dict, name: str) -> list[str]:
    eq = [str(e).lower().strip() for e in (ex.get("equipment") or []) if e]
    blob = name.lower()
    if eq == ["dumbbell"] and not re.search(r"\b(db|dumbbell)\b", blob):
        return ["bodyweight"]
    return eq or ["bodyweight"]


def enrich_exercise(ex: dict) -> dict:
    item = deepcopy(ex)
    name = f"{item.get('name', '')} {item.get('family', '')}"
    impact = "high" if item.get("pattern") in HIGH_IMPACT_PATTERNS or HIGH_IMPACT_NAME.search(name) else "low"
    laterality = item.get("laterality")
    if not laterality:
        laterality = "unilateral" if UNILATERAL.search(name) else "bilateral"
    item["impact"] = item.get("impact") or impact
    item["laterality"] = laterality
    item["equipment"] = _normalize_equipment(item, name)
    item["load_basis"] = item.get("load_basis") if "load_basis" in item else _load_basis(item)
    item["contraindications"] = item.get("contraindications") or _contraindications(item, item["impact"])
    item["regression_ids"] = item.get("regression_ids") or []
    return item


def is_overhead_exercise(ex: dict) -> bool:
    blob = f"{ex.get('name', '')} {ex.get('family', '')} {' '.join(str(t) for t in ex.get('tags') or [])}"
    return bool(OVERHEAD.search(blob))


def is_jump_or_plyo(ex: dict) -> bool:
    if ex.get("pattern") in HIGH_IMPACT_PATTERNS or ex.get("impact") == "high":
        return True
    blob = f"{ex.get('name', '')} {ex.get('family', '')} {' '.join(str(t) for t in ex.get('tags') or [])}"
    return bool(JUMP_OR_PLY.search(blob))


def enrich_catalog(catalog: list[dict]) -> list[dict]:
    return [enrich_exercise(ex) for ex in catalog]
