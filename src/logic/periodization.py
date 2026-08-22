"""Mesocycle templates around an existing week JSON payload."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional

BLOCK_KEYS = ("ramp", "activation", "block_a", "block_b", "accessories")

DEFAULT_TEMPLATES = {
    "STOP": {
        "weeks": 1,
        "phases": ["referral"],
        "volume": [1.0],
        "intensity": [1.0],
        "retest_after_week": 1,
    },
    "MOBILITY": {
        "weeks": 4,
        "phases": ["build", "build", "build", "deload"],
        "volume": [1.0, 1.05, 1.1, 0.7],
        "intensity": [1.0, 1.0, 1.02, 0.85],
        "retest_after_week": 4,
    },
    "STABILITY": {
        "weeks": 4,
        "phases": ["build", "build", "intensify", "deload"],
        "volume": [1.0, 1.05, 1.1, 0.7],
        "intensity": [1.0, 1.03, 1.06, 0.85],
        "retest_after_week": 4,
    },
    "PATTERN": {
        "weeks": 4,
        "phases": ["build", "intensify", "intensify", "deload"],
        "volume": [1.0, 1.0, 0.95, 0.7],
        "intensity": [1.0, 1.05, 1.08, 0.85],
        "retest_after_week": 4,
    },
    "STRENGTH": {
        "weeks": 4,
        "phases": ["build", "intensify", "intensify", "deload"],
        "volume": [1.0, 0.95, 0.9, 0.65],
        "intensity": [1.0, 1.05, 1.08, 0.8],
        "retest_after_week": 4,
    },
    "POWER": {
        "weeks": 4,
        "phases": ["build", "intensify", "intensify", "deload"],
        "volume": [1.0, 0.9, 0.85, 0.65],
        "intensity": [1.0, 1.04, 1.08, 0.8],
        "retest_after_week": 4,
    },
}


def template_for(status: str, methodology: Optional[dict] = None) -> dict:
    table = (methodology or {}).get("mesocycle_by_status") or DEFAULT_TEMPLATES
    return deepcopy(table.get(status) or DEFAULT_TEMPLATES["PATTERN"])


def mesocycle_envelope(status: str, week_index: int = 1, methodology: Optional[dict] = None) -> dict:
    tmpl = template_for(status, methodology)
    length = int(tmpl.get("weeks") or 4)
    idx = max(1, min(int(week_index or 1), length))
    phases = tmpl.get("phases") or ["build"] * length
    phase = phases[idx - 1] if idx - 1 < len(phases) else phases[-1]
    return {
        "length": length,
        "week_index": idx,
        "phase": phase,
        "volume_factor": (tmpl.get("volume") or [1.0])[idx - 1],
        "intensity_factor": (tmpl.get("intensity") or [1.0])[idx - 1],
        "retest_due": idx >= int(tmpl.get("retest_after_week") or length),
        "retest_after_week": tmpl.get("retest_after_week") or length,
        "phases": phases,
    }


def _scale_sets(value, factor: float) -> int:
    try:
        sets = int(value)
    except (TypeError, ValueError):
        return value
    return max(1, int(round(sets * factor)))


def apply_week_progression(week_plan: dict, week_index: int, methodology: Optional[dict] = None) -> dict:
    """Copy an anchored week-1 plan and scale dose. Does not re-pick exercises."""
    plan = deepcopy(week_plan)
    status = plan.get("status") or (plan.get("analysis") or {}).get("status") or "PATTERN"
    env = mesocycle_envelope(status, week_index, methodology)
    vol = float(env["volume_factor"])
    inten = float(env["intensity_factor"])
    phase = env["phase"]
    for day in plan.get("days") or []:
        for key, items in (day.get("blocks") or {}).items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or item.get("unfilled"):
                    continue
                if key in {"block_a", "block_b", "accessories"}:
                    item["sets"] = _scale_sets(item.get("sets"), vol)
                    intensity = item.get("intensity") or 0
                    if intensity:
                        item["intensity"] = round(float(intensity) * inten, 3)
                        if item.get("percent_1rm"):
                            item["percent_1rm"] = int(round(item["intensity"] * 100))
                            if item.get("one_rm"):
                                load = round(float(item["one_rm"]) * item["intensity"] / 2.5) * 2.5
                                item["load"] = load
                                item["load_kg"] = load
                if phase == "deload":
                    rpe = item.get("rpe")
                    if rpe not in (None, ""):
                        try:
                            item["rpe"] = max(4, float(rpe) - 1)
                        except (TypeError, ValueError):
                            pass
    if phase == "deload":
        for cell in plan.get("calendar") or []:
            if cell.get("kind") == "gym":
                cell["kind"] = "deload"
                cell["tone"] = ((methodology or {}).get("kind_tones") or {}).get("deload", "warn")
                cell["label"] = "deload"
                cell["notes"] = ((methodology or {}).get("recovery_presets") or {}).get("deload", {}).get(
                    "notes"
                ) or "Cut volume. Technique and mobility only."
        plan["week_type"] = "deload"
        plan["week_title"] = f"Deload week {env['week_index']} of {env['length']}"
    else:
        plan["week_title"] = (
            f"{status.title()} {phase} week {env['week_index']} of {env['length']}"
        )
        plan["week_type"] = phase
    plan["schema_version"] = max(int(plan.get("schema_version") or 2), 3)
    plan["mesocycle"] = env
    plan["week_index"] = env["week_index"]
    return plan


def stamp_week_one(plan: dict, methodology: Optional[dict] = None) -> dict:
    status = plan.get("status") or "PATTERN"
    env = mesocycle_envelope(status, 1, methodology)
    plan = deepcopy(plan)
    plan["schema_version"] = max(int(plan.get("schema_version") or 2), 3)
    plan["mesocycle"] = env
    plan["week_index"] = 1
    plan["block_id"] = plan.get("block_id")
    return plan
