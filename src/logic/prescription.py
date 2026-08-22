"""Slot-based weekly program assembly from the ingested catalog."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from src.logic.catalog_enrich import enrich_catalog, is_jump_or_plyo, is_overhead_exercise
from src.logic.fms_analyzer import analyze_fms_profile
from src.logic.needs_engine import build_need_bundle
from src.logic.periodization import stamp_week_one
from src.logic.taste import prior_contribution
from src.taxonomy import FAULT_TO_TAG_MAP

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data/processed/exercise_catalog.json"
METHODOLOGY_PATH = ROOT / "data/processed/methodology.json"

BLOCK_KEYS = ("ramp", "activation", "block_a", "block_b", "accessories")
_catalog_cache: Optional[list[dict]] = None
_methodology_cache: Optional[dict] = None
_catalog_mtime: Optional[float] = None
_methodology_mtime: Optional[float] = None

UNILATERAL_MARKERS = ("SINGLE", "SPLIT", "SA ", "OFFSET", "SUITCASE", "UNILATERAL", "1-ARM", "1 ARM")
ASYM_FAULTS = ("asymmetry", "uneven", "left_side", "right_side", "lateral_shift")
DEFAULT_KIT = {"bodyweight", "band", "bands", "wall", "none", "floor"}


def athlete_kit(equipment: Optional[list] = None) -> set[str]:
    raw = equipment
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = [raw]
    items = {
        str(item).lower().strip().replace(" ", "_")
        for item in (raw or [])
        if item not in (None, "", "[]")
    }
    items.discard("[]")
    if not items:
        return set(DEFAULT_KIT)
    items.update({"bodyweight", "none"})
    if "band" in items:
        items.add("bands")
    if "bands" in items:
        items.add("band")
    return items


def load_catalog() -> list[dict]:
    global _catalog_cache, _catalog_mtime
    mtime = CATALOG_PATH.stat().st_mtime
    if _catalog_cache is None or _catalog_mtime != mtime:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            _catalog_cache = enrich_catalog(json.load(f))
        _catalog_mtime = mtime
    return _catalog_cache


def load_methodology() -> dict:
    global _methodology_cache, _methodology_mtime
    mtime = METHODOLOGY_PATH.stat().st_mtime
    if _methodology_cache is None or _methodology_mtime != mtime:
        with open(METHODOLOGY_PATH, encoding="utf-8") as f:
            _methodology_cache = json.load(f)
        _methodology_mtime = mtime
    return _methodology_cache


def context_key(analysis: dict) -> str:
    faults = sorted({f.get("fault") for f in analysis.get("faults", []) if f.get("fault")})
    return "|".join(
        [f"level_{analysis.get('target_level', 1)}", analysis.get("status", "PATTERN")] + faults[:4]
    )


def _search_tags(analysis: dict, bundle: Optional[dict] = None) -> set[str]:
    tags = {f"level_{analysis.get('target_level', 1)}"}
    scores = analysis.get("effective_scores", {})
    mapping = {
        "overhead_squat": "pattern_squat",
        "hurdle_step": "pattern_step",
        "inline_lunge": "pattern_lunge",
        "shoulder_mobility": "pattern_shoulder",
        "active_straight_leg_raise": "pattern_leg_raise",
        "trunk_stability_pushup": "pattern_pushup",
        "rotary_stability": "pattern_rotary",
    }
    for test, tag in mapping.items():
        if scores.get(test, 3) <= 2:
            tags.add(tag)
    for fault in analysis.get("faults", []):
        mapped = FAULT_TO_TAG_MAP.get(fault.get("fault"))
        if mapped:
            tags.add(mapped)
        name = (fault.get("fault") or "").lower()
        if any(token in name for token in ASYM_FAULTS):
            tags.update({"fix_asymmetry", "unilateral"})
    if bundle:
        tags.update(bundle.get("search_tags") or [])
    return tags


def score_exercise(ex: dict, tags: set[str], target_level: int, priors: dict, ctx: str, *, used_week: Optional[set] = None) -> tuple[float, dict]:
    ex_tags = {str(t).lower() for t in ex.get("tags", [])}
    need_match = sum(1 for t in tags if t.lower() in ex_tags)
    if any(t.startswith("fix_") and t.lower() in ex_tags for t in tags):
        need_match += 3
    if "unilateral" in tags and (ex.get("laterality") == "unilateral"):
        need_match += 1.5
    level = ex.get("level", 1)
    level_fit = max(0, 4 - abs(level - max(target_level, 1)))
    taste = prior_contribution(priors, ex["id"], ctx)
    novelty = -0.35 if used_week and ex["id"] in used_week else 0.0
    total = need_match + level_fit + taste["score"] + novelty
    breakdown = {
        "need_match": round(need_match, 3),
        "level_fit": round(level_fit, 3),
        "taste": taste["score"],
        "taste_applied": taste["applied"],
        "taste_label": taste["label"],
        "taste_n": taste["sample_size"],
        "novelty": novelty,
        "total": round(total, 3),
    }
    return total, breakdown


def _round_load(value: float, increment: float = 2.5) -> float:
    if value <= 0:
        return 0
    return round(value / increment) * increment


def _format_rest(sec: Optional[int]) -> str:
    if not sec:
        return ""
    sec = int(sec)
    if sec >= 60 and sec % 60 == 0:
        return f"{sec // 60}min"
    if sec >= 60:
        minutes, rem = divmod(sec, 60)
        return f"{minutes}:{rem:02d}"
    return f"{sec}s"


def _dose_for(status: str, section: str, methodology: dict) -> dict:
    table = methodology.get("dose_by_status", {}).get(status) or methodology["dose_by_status"]["PATTERN"]
    key = methodology.get("dose_key_by_section", {}).get(section, section)
    if key in {"warmup", "activation"}:
        key = "warmup"
    if key in {"accessories", "accessory"}:
        key = "accessory"
    if key in {"block_a", "main"}:
        key = "main"
    if key in {"block_b", "backdown"}:
        key = "backdown"
    return deepcopy(table.get(key) or table.get("accessory") or {"sets": 2, "reps": "8", "rpe": 6, "intensity": 0, "rest_sec": 60, "tempo": "Controlled"})


def _rpe_from_dose(dose: dict, intensity: float) -> Optional[float]:
    if dose.get("rpe") is not None:
        return float(dose["rpe"])
    if intensity:
        return float(max(5, min(10, round(intensity * 10))))
    return None


def _reps_rpe(reps: Any, rpe: Optional[float]) -> str:
    reps_s = str(reps or "").strip()
    primary = reps_s.split("-")[0].strip() if reps_s else ""
    if not primary:
        return ""
    if rpe is None:
        return primary
    rpe_s = str(int(rpe) if float(rpe).is_integer() else rpe)
    return f"{primary}-{rpe_s}"


def _apply_load(item: dict, lift_maxes: dict, ex: dict, methodology: dict) -> dict:
    intensity = item.get("intensity") or 0
    lift_key = ex.get("load_basis")
    if lift_key is None:
        item["percent_1rm"] = None
        item["one_rm"] = None
        item["load"] = None
        item["load_kg"] = None
        item["intensity_label"] = item.get("reps_rpe") or "bodyweight / technique"
        return item
    if lift_key == "pattern":
        lift_key = methodology.get("lift_key_by_pattern", {}).get(ex.get("pattern"))
    one_rm = None
    if lift_key:
        raw = lift_maxes.get(lift_key) or lift_maxes.get(ex.get("pattern"))
        if raw not in (None, ""):
            one_rm = float(raw)
    if not lift_key:
        item["percent_1rm"] = None
        item["one_rm"] = None
        item["load"] = None
        item["load_kg"] = None
        item["intensity_label"] = item.get("reps_rpe") or "bodyweight / technique"
        return item
    percent = int(round(float(intensity) * 100)) if intensity else None
    item["percent_1rm"] = percent
    item["one_rm"] = one_rm
    if intensity and one_rm:
        load = _round_load(float(one_rm) * float(intensity), methodology.get("load_rounding", 2.5))
        item["load"] = load
        item["load_kg"] = load
        item["intensity_label"] = item.get("reps_rpe") or f"{percent}% 1RM"
    elif item.get("reps_rpe"):
        item["load"] = None
        item["load_kg"] = None
        item["intensity_label"] = item["reps_rpe"]
    else:
        item["load"] = None
        item["load_kg"] = None
        item["intensity_label"] = "bodyweight / technique"
    return item


def _slot_role(slot: dict, methodology: dict) -> str:
    if slot.get("display_role"):
        return str(slot["display_role"]).upper()
    token = slot.get("token")
    table = methodology.get("slot_roles") or {}
    template = table.get(token) or table.get(slot.get("ramp_role")) or ""
    pattern = (slot.get("pattern") or "").upper()
    if template:
        return template.replace("{PATTERN}", pattern or "MOVE")
    mapped = (methodology.get("role_by_pattern") or {}).get(slot.get("pattern"))
    if mapped:
        return mapped
    return (slot.get("ramp_role") or slot.get("pattern") or "ACC").upper()


def _display_role(ex: dict, methodology: dict, slot: Optional[dict] = None) -> str:
    if slot:
        return _slot_role(slot, methodology)
    mapped = (methodology.get("role_by_pattern") or {}).get(ex.get("pattern"))
    if mapped:
        return mapped
    return (ex.get("ramp_role") or ex.get("pattern") or "ACC").upper()


def _why(ex: dict, analysis: dict, role: str, breakdown: Optional[dict] = None) -> str:
    faults = [
        str(f.get("fault", "")).replace("_", " ")
        for f in analysis.get("faults", [])[:2]
        if f.get("fault") and f.get("polarity") != "quality"
    ]
    needs = analysis.get("needs") or []
    bits = [role] if role else []
    if needs:
        bits.append("needs " + ", ".join(needs[:2]))
    if faults:
        bits.append("faults: " + ", ".join(faults))
    if breakdown:
        if breakdown.get("taste_applied"):
            bits.append(breakdown.get("taste_label") or "coach taste")
        elif breakdown.get("taste_n"):
            bits.append(breakdown.get("taste_label"))
        else:
            bits.append("methodology match")
    if ex.get("indications_text"):
        bits.append(str(ex["indications_text"])[:120])
    return " · ".join(b for b in bits if b)


def _to_item(ex: dict, dose: dict, comments: dict, analysis: dict, *, role: str, section: str, breakdown: Optional[dict] = None) -> dict:
    fault_bits = [
        f.get("fault", "").replace("_", " ")
        for f in analysis.get("faults", [])[:3]
        if f.get("polarity") != "quality"
    ]
    comment_bits = [f"{k}: {v}" for k, v in (comments or {}).items() if v][:2]
    cue = ex.get("indications_text") or ex.get("description") or ""
    if comment_bits:
        cue = (cue + " Coach note — " + "; ".join(comment_bits)).strip()
    elif fault_bits:
        cue = (cue + f" Address: {', '.join(fault_bits)}.").strip()
    intensity = dose.get("intensity", 0) or 0
    rpe = _rpe_from_dose(dose, intensity)
    reps = dose.get("reps", "8")
    rest_sec = dose.get("rest_sec", 60)
    return {
        "exercise_id": ex["id"],
        "name": ex["name"],
        "role": role,
        "tag": role,
        "section": section,
        "sets": dose.get("sets", 2),
        "reps": reps,
        "rpe": rpe,
        "reps_rpe": _reps_rpe(reps, rpe),
        "intensity": intensity,
        "rest_sec": rest_sec,
        "rest": _format_rest(rest_sec),
        "tempo": dose.get("tempo", "Controlled"),
        "coach_note": cue[:400],
        "why": _why(ex, analysis, role, breakdown),
        "why_parts": {
            "methodology": role,
            "needs": (analysis.get("needs") or [])[:2],
            "faults": fault_bits,
            "taste": (breakdown or {}).get("taste_label"),
            "taste_applied": (breakdown or {}).get("taste_applied", False),
        },
        "score_breakdown": breakdown or {},
        "pattern": ex.get("pattern"),
        "program_role": ex.get("program_role"),
        "candidates": [],
    }


def _pattern_ok(ex: dict, pattern: Optional[str]) -> bool:
    if not pattern:
        return True
    return ex.get("pattern") == pattern


def _family_ok(ex: dict, family_contains: Optional[str]) -> bool:
    if not family_contains:
        return True
    blob = f"{ex.get('family', '')} {ex.get('name', '')}".upper()
    return family_contains.upper() in blob


def _eligible(
    ex: dict,
    *,
    hard: dict,
    restrictions: list[dict],
    equipment: Optional[set],
    status: str,
    scores: dict,
) -> tuple[bool, list[str]]:
    reasons = []
    if hard.get("pattern") and not _pattern_ok(ex, hard["pattern"]):
        reasons.append(f"pattern!={hard['pattern']}")
    if hard.get("ramp_role") and ex.get("ramp_role") != hard["ramp_role"]:
        reasons.append(f"ramp_role!={hard['ramp_role']}")
    if hard.get("max_level") is not None and ex.get("level", 99) > hard["max_level"]:
        reasons.append("above_max_level")
    if equipment:
        eq = {str(e).lower().strip().replace(" ", "_") for e in (ex.get("equipment") or []) if e}
        if not eq:
            eq = {"bodyweight"}
        if "bands" in eq:
            eq.add("band")
        if "band" in eq:
            eq.add("bands")
        name = f"{ex.get('name', '')} {ex.get('family', '')}".lower()
        if re.search(r"\btrap bar\b", name) and not ({"trap_bar", "trapbar"} & equipment):
            reasons.append("equipment")
        elif re.search(r"\b(barbell|\bbb\b)\b", name) and "barbell" not in equipment and "bodyweight" not in eq:
            reasons.append("equipment")
        elif not (eq & equipment):
            reasons.append("equipment")
    contra = set(ex.get("contraindications") or [])
    if status in contra:
        reasons.append(f"contraindicated:{status}")
    blocked = {b for r in restrictions for b in (r.get("blocks") or [])}
    if ex.get("pattern") in blocked:
        reasons.append(f"blocked_pattern:{ex.get('pattern')}")
    if ("high_impact" in blocked or "plyo" in blocked or "jump" in blocked) and is_jump_or_plyo(ex):
        reasons.append("jump_or_plyo_blocked")
    if ("overhead" in blocked or scores.get("shoulder_mobility", 3) <= 1) and is_overhead_exercise(ex):
        reasons.append("overhead_blocked")
    if "shoulder_mobility<=1" in contra and (
        scores.get("shoulder_mobility", 3) <= 1 or "overhead" in blocked
    ):
        reasons.append("shoulder_restriction")
    if "loaded_main" in blocked and ex.get("program_role") == "main" and ex.get("load_basis"):
        reasons.append("loaded_main_blocked")
    return (len(reasons) == 0, reasons)


def _soft_ok(ex: dict, soft: dict) -> bool:
    if soft.get("program_role") and ex.get("program_role") != soft["program_role"]:
        return False
    if soft.get("family_contains") and not _family_ok(ex, soft["family_contains"]):
        return False
    if soft.get("required_tag"):
        blob = " ".join(
            [str(t) for t in ex.get("tags", [])] + [ex.get("name") or "", ex.get("family") or ""]
        ).lower()
        if soft["required_tag"].lower() not in blob:
            return False
    return True


def _pick(
    catalog: list[dict],
    *,
    tags: set[str],
    target_level: int,
    priors: dict,
    ctx: str,
    count: int,
    pattern: Optional[str] = None,
    ramp_role: Optional[str] = None,
    program_role: Optional[str] = None,
    family_contains: Optional[str] = None,
    required_tag: Optional[str] = None,
    used: Optional[set] = None,
    max_level: Optional[int] = None,
    restrictions: Optional[list] = None,
    equipment: Optional[set] = None,
    status: str = "PATTERN",
    scores: Optional[dict] = None,
    used_session: Optional[set] = None,
    hard_keys: Optional[set] = None,
) -> tuple[list[tuple[dict, dict]], list[dict], list[str]]:
    used_week = used if used is not None else set()
    session = used_session if used_session is not None else set()
    restrictions = restrictions or []
    scores = scores or {}
    hard = {}
    soft = {}
    keys = hard_keys or set()
    mapping = {
        "pattern": pattern,
        "ramp_role": ramp_role,
        "max_level": max_level,
        "program_role": program_role,
        "family_contains": family_contains,
        "required_tag": required_tag,
    }
    for key, value in mapping.items():
        if value in (None, "", []):
            continue
        if key in {"pattern", "ramp_role", "max_level"} or key in keys:
            hard[key] = value
        else:
            soft[key] = value
    if ramp_role:
        hard["ramp_role"] = ramp_role

    def collect(apply_soft: bool, skip_week: bool = True) -> list[tuple[float, dict, dict]]:
        scored = []
        for ex in catalog:
            if ex["id"] in session:
                continue
            if skip_week and ex["id"] in used_week:
                continue
            ok, _reasons = _eligible(
                ex, hard=hard, restrictions=restrictions, equipment=equipment, status=status, scores=scores
            )
            if not ok:
                continue
            if apply_soft and not _soft_ok(ex, soft):
                continue
            total, breakdown = score_exercise(
                ex, tags, target_level, priors, ctx, used_week=used_week
            )
            scored.append((total, ex, breakdown))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    scored = collect(apply_soft=True, skip_week=True)
    if not scored and used_week:
        scored = collect(apply_soft=True, skip_week=False)
    if not scored and soft:
        scored = collect(apply_soft=False, skip_week=True)
    if not scored and soft:
        scored = collect(apply_soft=False, skip_week=False)
    selected = [(ex, breakdown) for _, ex, breakdown in scored[:count]]
    candidates = [ex for _, ex, _ in scored[:8]]
    reasons = []
    if not selected:
        bits = [f"{k}={v}" for k, v in hard.items()]
        reasons = ["no_eligible_match:" + ",".join(bits) if bits else "no_eligible_match"]
    for ex, _ in selected:
        session.add(ex["id"])
        used_week.add(ex["id"])
    return selected, candidates, reasons


def _finish_item(
    ex: dict,
    dose: dict,
    comments: dict,
    analysis: dict,
    lift_maxes: dict,
    methodology: dict,
    *,
    role: str,
    section: str,
    cands: list[dict],
    rest_sec: Optional[int] = None,
    breakdown: Optional[dict] = None,
) -> dict:
    item = _to_item(ex, dose, comments, analysis, role=role, section=section, breakdown=breakdown)
    if rest_sec is not None:
        item["rest_sec"] = rest_sec
        item["rest"] = _format_rest(rest_sec)
    item["candidates"] = [c["id"] for c in cands if c["id"] != ex["id"]]
    return _apply_load(item, lift_maxes, ex, methodology)


def _unfilled_item(slot: dict, methodology: dict, section: str, reasons: list[str], cands: list[dict]) -> dict:
    role = _slot_role(slot, methodology)
    return {
        "exercise_id": None,
        "name": "Unfilled slot",
        "role": role,
        "tag": role,
        "section": section,
        "unfilled": True,
        "unfilled_reasons": reasons,
        "sets": None,
        "reps": None,
        "rpe": None,
        "reps_rpe": "",
        "intensity": 0,
        "rest_sec": None,
        "rest": "",
        "tempo": "",
        "coach_note": "No eligible exercise matched hard constraints. Choose a candidate or leave empty.",
        "why": " · ".join(reasons) or "No eligible match",
        "why_parts": {"methodology": role, "needs": [], "faults": [], "taste": None, "taste_applied": False},
        "score_breakdown": {},
        "pattern": slot.get("pattern"),
        "program_role": slot.get("program_role"),
        "candidates": [c["id"] for c in cands],
    }


def _record_candidates(store: dict, key: str, cands: list[dict]) -> None:
    store[key] = [{"exercise_id": c["id"], "name": c["name"], "pattern": c.get("pattern")} for c in cands]


def _pick_env(analysis: dict, env: Optional[dict] = None) -> dict:
    extra = env or {}
    return {
        "restrictions": extra.get("restrictions") or [],
        "equipment": extra.get("equipment"),
        "status": analysis.get("status") or "PATTERN",
        "scores": analysis.get("effective_scores") or {},
        "used_session": extra.get("used_session"),
    }


def _fill_ramp(
    catalog: list[dict],
    methodology: dict,
    analysis: dict,
    tags: set[str],
    priors: dict,
    ctx: str,
    used: set[str],
    comments: dict,
    lift_maxes: dict,
    all_candidates: dict,
    env: Optional[dict] = None,
) -> list[dict]:
    items = []
    dose = _dose_for(analysis["status"], "ramp", methodology)
    target_level = min(analysis.get("target_level") or 1, 4)
    extra = _pick_env(analysis, env)
    session = extra["used_session"] if extra["used_session"] is not None else set()
    extra["used_session"] = session
    for ramp_role, n in methodology["slots"]["ramp"].items():
        selected, cands, reasons = _pick(
            catalog,
            tags=tags,
            target_level=target_level,
            priors=priors,
            ctx=ctx,
            count=n,
            ramp_role=ramp_role,
            used=used,
            **extra,
        )
        if not selected:
            slot = {"token": ramp_role, "ramp_role": ramp_role, "pattern": "warmup"}
            items.append(_unfilled_item(slot, methodology, "ramp", reasons, cands))
            continue
        for ex, breakdown in selected:
            items.append(
                _finish_item(
                    ex, dose, comments, analysis, lift_maxes, methodology,
                    role=(ramp_role or "PREP").upper(),
                    section="ramp",
                    cands=cands,
                    breakdown=breakdown,
                )
            )
            _record_candidates(all_candidates, ex["id"], cands)
    return items


def _fill_activation(
    catalog: list[dict],
    methodology: dict,
    analysis: dict,
    tags: set[str],
    priors: dict,
    ctx: str,
    used: set[str],
    comments: dict,
    lift_maxes: dict,
    all_candidates: dict,
    env: Optional[dict] = None,
) -> list[dict]:
    items = []
    dose = _dose_for(analysis["status"], "activation", methodology)
    extra = _pick_env(analysis, env)
    selected, cands, reasons = _pick(
        catalog,
        tags=tags,
        target_level=analysis.get("target_level") or 1,
        priors=priors,
        ctx=ctx,
        count=methodology["slots"].get("activation", 1),
        program_role="activation",
        used=used,
        **extra,
    )
    if not selected:
        items.append(
            _unfilled_item(
                {"token": "activation", "program_role": "activation"},
                methodology,
                "activation",
                reasons,
                cands,
            )
        )
        return items
    for ex, breakdown in selected:
        items.append(
            _finish_item(
                ex, dose, comments, analysis, lift_maxes, methodology,
                role="ACTIVATION",
                section="activation",
                cands=cands,
                breakdown=breakdown,
            )
        )
        _record_candidates(all_candidates, ex["id"], cands)
    return items


def _fill_circuit(
    slots: list[dict],
    section: str,
    catalog: list[dict],
    methodology: dict,
    analysis: dict,
    tags: set[str],
    priors: dict,
    ctx: str,
    used: set[str],
    comments: dict,
    lift_maxes: dict,
    all_candidates: dict,
    *,
    max_level: Optional[int] = None,
    as_circuit: bool = True,
    env: Optional[dict] = None,
) -> list[dict]:
    items = []
    circuit = methodology.get("circuit") or {}
    loaded_patterns = set((methodology.get("lift_key_by_pattern") or {}).keys())
    target_level = analysis.get("target_level") or 1
    extra = _pick_env(analysis, env)
    for slot in slots:
        if slot.get("ramp_role") or slot.get("pattern") == "warmup":
            dose_section = "ramp"
        elif slot.get("program_role") == "main" or slot.get("pattern") in loaded_patterns:
            dose_section = section
        else:
            dose_section = "accessories"
        dose = _dose_for(analysis["status"], dose_section, methodology)
        intra = circuit.get("intra_rest_sec", dose.get("rest_sec", 45)) if as_circuit else dose.get("rest_sec", 60)
        hard_keys = set()
        if slot.get("token") in (methodology.get("hard_constraints_by_token") or {}):
            hard_keys = set((methodology.get("hard_constraints_by_token") or {}).get(slot["token"]) or [])
        selected, cands, reasons = _pick(
            catalog,
            tags=tags,
            target_level=target_level,
            priors=priors,
            ctx=ctx,
            count=1,
            pattern=slot.get("pattern"),
            program_role=slot.get("program_role"),
            ramp_role=slot.get("ramp_role"),
            family_contains=slot.get("family_contains"),
            required_tag=slot.get("required_tag"),
            used=used,
            max_level=max_level,
            hard_keys=hard_keys,
            **extra,
        )
        if not selected:
            item = _unfilled_item(slot, methodology, section, reasons, cands)
            item["rest_sec"] = intra
            item["rest"] = _format_rest(intra)
            items.append(item)
            if cands:
                _record_candidates(all_candidates, f"unfilled:{section}:{slot.get('token')}", cands)
            continue
        for ex, breakdown in selected:
            role = _display_role(ex, methodology, slot)
            items.append(
                _finish_item(
                    ex, dose, comments, analysis, lift_maxes, methodology,
                    role=role,
                    section=section,
                    cands=cands,
                    rest_sec=intra,
                    breakdown=breakdown,
                )
            )
            _record_candidates(all_candidates, ex["id"], cands)
    block_rest = circuit.get("block_rest_sec", 120)
    if as_circuit and items:
        items[-1]["rest_sec"] = block_rest
        items[-1]["rest"] = _format_rest(block_rest)
        items[-1]["circuit_end"] = True
    return items


def _week_type(status: str, methodology: dict) -> str:
    return methodology.get("week_type_by_status", {}).get(status, "build")


def _block_meta(methodology: dict) -> dict:
    circuit = methodology.get("circuit") or {}
    meta = {}
    for key, spec in (methodology.get("section_labels") or {}).items():
        entry = dict(spec)
        if entry.get("format") == "circuit":
            entry.setdefault("block_rest_sec", circuit.get("block_rest_sec", 120))
            entry.setdefault("intra_rest_sec", circuit.get("intra_rest_sec", 45))
        meta[key] = entry
    return meta


def _emphasis_patterns(analysis: dict, methodology: dict, catalog: list[dict]) -> list[str]:
    available = {ex.get("pattern") for ex in catalog if ex.get("pattern")}
    scores = analysis.get("effective_scores") or {}
    mapping = methodology.get("test_to_pattern") or {}
    ranked = sorted(mapping.items(), key=lambda kv: (scores.get(kv[0], 3), kv[0]))
    ordered: list[str] = []
    for _, pattern in ranked:
        if pattern in available and pattern not in ordered:
            ordered.append(pattern)
    for pattern in methodology.get("coverage_patterns") or []:
        if pattern in available and pattern not in ordered:
            ordered.append(pattern)
    return ordered or [p for p in available if p != "warmup"]


def _resolve_slot_token(token: str, primary: str, secondary: str, analysis: dict, methodology: dict) -> dict:
    status = analysis.get("status")
    if token == "primary":
        return {"token": token, "pattern": primary, "program_role": "main"}
    if token == "secondary":
        return {"token": token, "pattern": secondary, "program_role": "main"}
    if token == "corrective":
        faults = [f for f in (analysis.get("faults") or []) if f.get("polarity") != "quality"]
        if faults:
            tag = FAULT_TO_TAG_MAP.get(faults[0].get("fault"))
            if tag:
                return {"token": token, "required_tag": tag}
        return {"token": token, "pattern": "core"}
    if token in {"plyo", "speed"} and status in {"MOBILITY", "STABILITY", "STOP"}:
        return {"token": "gait", "pattern": "gait"}
    program_role = None
    if token in {"squat", "lunge", "hinge", "push", "pull"}:
        program_role = "main"
    elif token in {"plyo", "speed"}:
        program_role = "power"
    elif token == "warmup":
        return {"token": token, "pattern": "warmup", "ramp_role": "mobilize"}
    return {"token": token, "pattern": token, "program_role": program_role}


def _day_slots(day_idx: int, patterns: list[str], analysis: dict, methodology: dict) -> dict:
    primary = patterns[day_idx % len(patterns)]
    secondary = patterns[(day_idx + 1) % max(len(patterns), 1)]
    blueprint = methodology.get("slot_blueprint") or {}
    return {
        section: [
            _resolve_slot_token(token, primary, secondary, analysis, methodology)
            for token in tokens
        ]
        for section, tokens in blueprint.items()
    }


def _session_title(blocks: dict) -> str:
    roles = []
    for key in ("block_a", "block_b", "accessories"):
        for item in blocks.get(key) or []:
            role = item.get("role")
            if role and role not in roles:
                roles.append(role)
            if len(roles) >= 4:
                return " | ".join(roles)
    return " | ".join(roles) or "SESSION"


def _gym_indices(count: int, span: int = 7) -> list[int]:
    if count <= 0:
        return []
    count = min(count, span)
    return [int(i * span / count) for i in range(count)]


def _kind_for_gap(index: int, gym_set: set[int], span: int = 7) -> str:
    if any(abs(index - gym) == 1 for gym in gym_set):
        return "active_recovery"
    if index >= span - 2:
        return "rest" if index == span - 1 else "passive_recovery"
    return "rest"


def _build_calendar(days: list[dict], days_per_week: int, methodology: dict, analysis: dict) -> list[dict]:
    weekdays = methodology.get("weekdays") or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    span = len(weekdays)
    gym_idx = _gym_indices(len(days), span)
    gym_set = set(gym_idx)
    gym_by_pos = {pos: days[i] for i, pos in enumerate(gym_idx) if i < len(days)}
    presets = methodology.get("recovery_presets") or {}
    tones = methodology.get("kind_tones") or {}
    faults = [str(f.get("fault", "")).replace("_", " ") for f in (analysis.get("faults") or [])[:2] if f.get("fault")]
    calendar = []
    for i, weekday in enumerate(weekdays):
        if i in gym_set:
            session = gym_by_pos.get(i) or {}
            kind = session.get("session_kind") or "gym"
            notes = " / ".join(session.get("emphasis") or [])
            if faults and not notes:
                notes = "Address: " + ", ".join(faults)
            calendar.append({
                "weekday": weekday,
                "kind": kind,
                "tone": tones.get(kind, "accent"),
                "label": kind.replace("_", " "),
                "day": session.get("day"),
                "title": session.get("title") or "Gym",
                "notes": notes,
                "done": False,
            })
        else:
            kind = "referral" if analysis.get("status") == "STOP" else _kind_for_gap(i, gym_set, span)
            preset = presets.get(kind) or {"title": kind.replace("_", " ").title(), "notes": ""}
            notes = preset.get("notes") or ""
            if kind == "active_recovery" and faults:
                notes = f"{notes} Focus: {', '.join(faults)}."
            calendar.append({
                "weekday": weekday,
                "kind": kind,
                "tone": tones.get(kind, "muted"),
                "label": kind.replace("_", " "),
                "day": None,
                "title": preset.get("title"),
                "notes": notes,
                "done": False,
            })
    return calendar


def _analysis_payload(analysis: dict) -> dict:
    return {
        "reason": analysis.get("reason"),
        "effective_scores": analysis["effective_scores"],
        "total_score": analysis["total_score"],
        "needs": analysis["needs"],
        "target_level": analysis["target_level"],
        "status": analysis["status"],
        "faults": analysis["faults"],
        "comments": analysis["comments"],
        "movement_needs": analysis.get("movement_needs") or [],
        "restrictions": analysis.get("restrictions") or [],
    }


def assemble_weekly_program(
    profile: dict,
    *,
    days_per_week: int = 3,
    lift_maxes: Optional[dict] = None,
    priors: Optional[dict] = None,
    use_manual_scores: bool = False,
    equipment: Optional[list] = None,
) -> dict:
    analysis = analyze_fms_profile(profile, use_manual_scores=use_manual_scores)
    methodology = load_methodology()
    catalog = load_catalog()
    lift_maxes = lift_maxes or {}
    priors = priors or {}
    bundle = build_need_bundle(analysis)
    analysis["movement_needs"] = bundle["needs"]
    analysis["restrictions"] = bundle["restrictions"]
    ctx = context_key(analysis)
    tags = _search_tags(analysis, bundle)

    days_per_week = max(methodology["min_days"], min(methodology["max_days"], int(days_per_week or 3)))
    used: set[str] = set()
    days = []
    all_candidates: dict[str, list[dict]] = {}
    comments = analysis.get("comments") or {}
    week_type = _week_type(analysis["status"], methodology)
    target_level = max(analysis.get("target_level") or 1, 1)
    patterns = _emphasis_patterns(analysis, methodology, catalog)
    meta = _block_meta(methodology)
    circuit = methodology.get("circuit") or {}
    eq = athlete_kit(equipment)
    fill_kw = dict(
        catalog=catalog,
        methodology=methodology,
        analysis=analysis,
        tags=tags,
        priors=priors,
        ctx=ctx,
        used=used,
        comments=comments,
        lift_maxes=lift_maxes,
        all_candidates=all_candidates,
    )

    def env_for_day() -> dict:
        return {
            "restrictions": bundle["restrictions"],
            "equipment": eq,
            "used_session": set(),
        }

    if analysis["status"] == "STOP":
        env = env_for_day()
        blocks = {
            "ramp": _fill_ramp(**fill_kw, env=env),
            "activation": [],
            "block_a": [],
            "block_b": [],
            "accessories": [],
        }
        days = [{
            "day": 1,
            "title": _session_title(blocks) or "MOBILITY ONLY",
            "emphasis": patterns[:2] or ["mobility"],
            "session_kind": "referral",
            "blocks": blocks,
            "block_meta": meta,
        }]
        plan = {
            "schema_version": 3,
            "week_title": analysis.get("reason") or "Medical referral — no loaded training",
            "week_type": week_type,
            "needs_summary": analysis["reason"],
            "status": "STOP",
            "referral": True,
            "analysis": _analysis_payload(analysis),
            "context_key": ctx,
            "days": days,
            "calendar": _build_calendar([], 0, methodology, analysis),
            "ui": {
                "section_order": list(BLOCK_KEYS),
                "kind_tones": methodology.get("kind_tones") or {},
                "circuit": circuit,
            },
            "candidate_exercises": all_candidates,
            "ai_plan_frozen": True,
        }
        return stamp_week_one(plan, methodology)

    for day_idx in range(days_per_week):
        slots = _day_slots(day_idx, patterns, analysis, methodology)
        primary = patterns[day_idx % len(patterns)] if patterns else None
        secondary = patterns[(day_idx + 1) % len(patterns)] if patterns else None
        env = env_for_day()
        blocks = {
            "ramp": _fill_ramp(**fill_kw, env=env),
            "activation": _fill_activation(**fill_kw, env=env),
            "block_a": _fill_circuit(
                slots.get("block_a") or [],
                "block_a",
                **fill_kw,
                max_level=target_level + 1,
                env=env,
            ),
            "block_b": _fill_circuit(
                slots.get("block_b") or [],
                "block_b",
                **fill_kw,
                max_level=max(target_level, 1),
                env=env,
            ),
            "accessories": _fill_circuit(
                slots.get("accessories") or [],
                "accessories",
                **fill_kw,
                as_circuit=False,
                env=env,
            ),
        }
        days.append({
            "day": day_idx + 1,
            "title": _session_title(blocks),
            "emphasis": [p for p in (primary, secondary) if p],
            "session_kind": "gym",
            "blocks": blocks,
            "block_meta": meta,
        })

    plan = {
        "schema_version": 3,
        "week_title": f"{analysis['status'].title()} {week_type} week — {days_per_week} gym sessions",
        "week_type": week_type,
        "needs_summary": analysis["reason"],
        "status": analysis["status"],
        "referral": False,
        "analysis": _analysis_payload(analysis),
        "context_key": ctx,
        "days": days,
        "calendar": _build_calendar(days, days_per_week, methodology, analysis),
        "ui": {
            "section_order": list(BLOCK_KEYS),
            "kind_tones": methodology.get("kind_tones") or {},
            "circuit": circuit,
        },
        "candidate_exercises": all_candidates,
        "ai_plan_frozen": True,
    }
    return stamp_week_one(plan, methodology)


def catalog_by_id() -> dict[str, dict]:
    return {ex["id"]: ex for ex in load_catalog()}
