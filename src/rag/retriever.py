import json
from typing import Dict, Any, Optional
from src.logic.prescription import assemble_weekly_program, load_catalog, score_exercise, _search_tags, context_key
from src.logic.fms_analyzer import analyze_fms_profile


async def get_exercises_by_profile(
    simple_scores: Dict[str, int],
    detailed_faults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile = detailed_faults or {k: {"score": v} for k, v in simple_scores.items()}
    profile.setdefault("use_manual_scores", not bool(detailed_faults))
    analysis = analyze_fms_profile(profile, use_manual_scores=profile.get("use_manual_scores", False))
    tags = _search_tags(analysis)
    ctx = context_key(analysis)
    catalog = load_catalog()
    scored = [
        {"ex": ex, "score": score_exercise(ex, tags, analysis.get("target_level") or 1, {}, ctx)}
        for ex in catalog
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = [x["ex"] for x in scored[:6]]
    return {"status": "SUCCESS", "analysis": analysis, "data": top}
