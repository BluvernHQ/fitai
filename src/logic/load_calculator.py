"""Sheet-backed 1RM % tables and pro-rata lift estimates."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
TABLES_PATH = ROOT / "data/processed/load_tables.json"


@lru_cache(maxsize=1)
def load_tables() -> dict:
    if not TABLES_PATH.exists():
        return {
            "version": "v1",
            "anchor_lift": "back_squat",
            "reps_rpe_percent": [],
            "rm_ladder": [],
            "pro_rata_from_back_squat": {"back_squat": 1.0},
        }
    return json.loads(TABLES_PATH.read_text(encoding="utf-8"))


def _as_float(value, default=None):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def percent_1rm_for(reps: int, rpe: float, tables: Optional[dict] = None) -> Optional[float]:
    tables = tables or load_tables()
    rows = tables.get("reps_rpe_percent") or []
    reps = int(reps)
    rpe = float(rpe)
    exact = next((r for r in rows if int(r["reps"]) == reps and float(r["rpe"]) == rpe), None)
    if exact:
        return float(exact["percent_1rm"])
    # nearest RPE for same reps
    same = [r for r in rows if int(r["reps"]) == reps]
    if not same:
        return None
    nearest = min(same, key=lambda r: abs(float(r["rpe"]) - rpe))
    return float(nearest["percent_1rm"])


def estimate_1rm(load_kg: float, reps: int, rpe: float = 10, tables: Optional[dict] = None) -> dict:
    """Estimate 1RM from performed load × reps × RPE using sheet % table."""
    load_kg = float(load_kg)
    pct = percent_1rm_for(reps, rpe, tables)
    if not pct or pct <= 0:
        # Epley fallback
        estimated = load_kg * (1 + reps / 30.0)
        return {
            "estimated_1rm": round(estimated, 1),
            "percent_1rm": None,
            "method": "epley_fallback",
            "load_kg": load_kg,
            "reps": reps,
            "rpe": rpe,
        }
    estimated = load_kg / pct
    return {
        "estimated_1rm": round(estimated, 1),
        "percent_1rm": pct,
        "method": "sheet_reps_rpe",
        "load_kg": load_kg,
        "reps": reps,
        "rpe": rpe,
    }


def load_for_percent(one_rm: float, percent: float) -> float:
    return round(float(one_rm) * float(percent), 1)


def pro_rata_maxes(anchor_1rm: float, anchor_lift: str = "back_squat", tables: Optional[dict] = None) -> dict:
    """Derive sister-lift maxes from an anchor (sheet ratios are vs back squat)."""
    tables = tables or load_tables()
    ratios = tables.get("pro_rata_from_back_squat") or {}
    anchor_1rm = float(anchor_1rm)
    if anchor_lift == "back_squat" or anchor_lift not in ratios:
        back = anchor_1rm if anchor_lift == "back_squat" else (
            anchor_1rm / float(ratios.get(anchor_lift) or 1.0)
        )
    else:
        back = anchor_1rm / float(ratios[anchor_lift])
    out = {}
    for lift, ratio in ratios.items():
        out[lift] = round(back * float(ratio), 1)
    return out


def rm_ladder_loads(one_rm: float, tables: Optional[dict] = None) -> list[dict]:
    tables = tables or load_tables()
    one_rm = float(one_rm)
    rows = []
    for row in tables.get("rm_ladder") or []:
        pct = float(row["percent_1rm"])
        rows.append(
            {
                "rm": int(row["rm"]),
                "percent_1rm": pct,
                "load_kg": round(one_rm * pct, 1),
            }
        )
    return rows
