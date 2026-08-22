"""Load versioned FMS spec and observation polarity."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "data/processed/fms_spec.json"

QUALITY_KEYS = {
    "upright_torso",
    "knees_track_over_toes",
    "heels_stay_down",
    "bar_aligned_over_mid_foot",
    "pelvis_stable",
    "knee_stable",
    "clears_hurdle_smoothly",
    "head_neutral",
    "trunk_upright",
    "knee_tracks_over_foot",
    "stable_throughout",
    "hands_within_fist_distance",
    "hands_within_hand_length",
    "no_compensation",
    "no_pain",
    "remains_flat",
    "gt_80_hip_flexion",
    "neutral_spine_maintained",
    "initiates_as_one_unit",
    "elbows_aligned",
    "smooth_controlled",
    "neutral_maintained",
    "symmetrical",
}

PAIN_KEYS = {"pain_reported", "clearing_pain"}


@lru_cache(maxsize=1)
def load_fms_spec() -> dict:
    if not SPEC_PATH.exists():
        return {"version": "v1", "movements": []}
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def polarity_index() -> dict[str, str]:
    index: dict[str, str] = {}
    spec = load_fms_spec()
    for movement in spec.get("movements") or []:
        for section in movement.get("sections") or []:
            for obs in section.get("observations") or []:
                key = obs.get("key")
                if not key:
                    continue
                polarity = (obs.get("polarity") or "").lower()
                if polarity in {"quality", "fault", "pain", "moderate"}:
                    index[key] = "pain" if polarity == "pain" else polarity
                elif key in PAIN_KEYS:
                    index[key] = "pain"
                elif key in QUALITY_KEYS:
                    index[key] = "quality"
                else:
                    index[key] = "fault"
    for key in QUALITY_KEYS:
        index.setdefault(key, "quality")
    for key in PAIN_KEYS:
        index.setdefault(key, "pain")
    return index


def observation_polarity(key: str) -> str:
    if not key:
        return "fault"
    if key in PAIN_KEYS:
        return "pain"
    return polarity_index().get(key, "quality" if key in QUALITY_KEYS else "fault")


def is_fault_observation(key: str) -> bool:
    return observation_polarity(key) in {"fault", "pain", "moderate"}
