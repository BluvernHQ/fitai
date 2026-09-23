"""Normalize modular assessment sessions and fuse battery results for prescription."""

from __future__ import annotations

from typing import Optional

from src.logic.batteries import (
    SCORERS,
    load_registry,
    score_beighton,
    score_breathing,
    score_bunkie,
    score_mcgill,
    score_muscular_endurance,
)
from src.logic.fms_analyzer import TEST_KEYS, analyze_fms_profile

FMS_KEYS = set(TEST_KEYS)


def is_session_payload(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    if isinstance(payload.get("batteries"), dict):
        return True
    if isinstance(payload.get("selected_batteries"), list):
        return True
    return False


def is_legacy_fms_payload(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    if is_session_payload(payload):
        return False
    return any(k in payload for k in FMS_KEYS)


def normalize_session(payload: dict) -> dict:
    """Accept legacy FMS-only or modular session JSON → canonical session."""
    if not isinstance(payload, dict):
        payload = {}

    if is_session_payload(payload):
        selected = list(payload.get("selected_batteries") or [])
        batteries = dict(payload.get("batteries") or {})
        if not selected:
            selected = [k for k in batteries.keys() if batteries.get(k)]
        # Legacy embed: FMS keys at top level alongside batteries
        if "fms" not in batteries and any(k in payload for k in FMS_KEYS):
            batteries["fms"] = {k: payload[k] for k in FMS_KEYS if k in payload}
            if "fms" not in selected:
                selected.append("fms")
        if not selected:
            selected = list(load_registry().get("default_selected") or ["fms"])
        return {
            "student_id": payload.get("student_id"),
            "selected_batteries": selected,
            "batteries": batteries,
            "use_manual_scores": bool(payload.get("use_manual_scores", False)),
            "athlete_context": payload.get("athlete_context") or {},
            "session_notes": payload.get("session_notes") or "",
        }

    # Legacy flat FMS
    fms = {k: payload[k] for k in FMS_KEYS if k in payload}
    for meta in ("use_manual_scores", "student_id"):
        if meta in payload and meta not in fms:
            pass
    return {
        "student_id": payload.get("student_id"),
        "selected_batteries": ["fms"] if fms else list(load_registry().get("default_selected") or ["fms"]),
        "batteries": {"fms": fms} if fms else {},
        "use_manual_scores": bool(payload.get("use_manual_scores", False)),
        "athlete_context": payload.get("athlete_context") or {},
        "session_notes": payload.get("session_notes") or "",
        "_legacy_fms": True,
    }


def _fms_profile_from_session(session: dict) -> dict:
    fms = session.get("batteries", {}).get("fms") or {}
    profile = dict(fms) if isinstance(fms, dict) else {}
    profile["use_manual_scores"] = session.get("use_manual_scores", False)
    return profile


def _score_non_fms(battery_id: str, data: dict, ctx: dict) -> dict:
    if battery_id == "breathing":
        return score_breathing(data or {})
    if battery_id == "beighton":
        return score_beighton(data or {}, age=ctx.get("age"))
    if battery_id == "mcgill":
        return score_mcgill(data or {})
    if battery_id == "bunkie":
        return score_bunkie(data or {})
    if battery_id == "muscular_endurance":
        return score_muscular_endurance(data or {}, gender=ctx.get("gender"))
    scorer = SCORERS.get(battery_id)
    if scorer:
        return scorer(data or {})
    return {"battery": battery_id, "findings": [], "recommendations": [], "needs_hints": []}


def _status_without_fms(battery_results: dict, needs: list[str]) -> tuple[str, int, str]:
    if "pain-stop" in needs:
        return "STOP", 0, "Pain / stop flagged outside FMS."
    if "stability" in needs and "asymmetry" in needs:
        return "STABILITY", 3, "Core / sling endurance asymmetry without FMS — bias motor control."
    if "stability" in needs:
        return "STABILITY", 3, "Trunk / sling endurance limitation without FMS."
    if "mobility" in needs:
        return "MOBILITY", 1, "Hypermobility / mobility priority without FMS — control before load."
    if "endurance" in needs or "breathing" in needs:
        return "STRENGTH", 4, "Capacity focus without FMS; keep technique conservative."
    return "PATTERN", 3, "No FMS — conservative pattern-focused programming."


def analyze_assessment_session(
    payload: dict,
    *,
    use_manual_scores: Optional[bool] = None,
    athlete_context: Optional[dict] = None,
) -> dict:
    session = normalize_session(payload)
    if use_manual_scores is not None:
        session["use_manual_scores"] = use_manual_scores
    ctx = {**(session.get("athlete_context") or {}), **(athlete_context or {})}

    selected = session.get("selected_batteries") or []
    batteries = session.get("batteries") or {}
    battery_results = {}
    findings = []
    recommendations = []
    extra_needs: list[str] = []

    fms_analysis = None
    if "fms" in selected and isinstance(batteries.get("fms"), dict) and batteries.get("fms"):
        fms_analysis = analyze_fms_profile(
            _fms_profile_from_session(session),
            use_manual_scores=session.get("use_manual_scores", False),
        )
        battery_results["fms"] = {
            "battery": "fms",
            "effective_scores": fms_analysis.get("effective_scores"),
            "side_scores": fms_analysis.get("side_scores"),
            "total_score": fms_analysis.get("total_score"),
            "status": fms_analysis.get("status"),
            "needs": fms_analysis.get("needs") or [],
            "faults": fms_analysis.get("faults") or [],
            "findings": [f"FMS total {fms_analysis.get('total_score', 0)}/21 — {fms_analysis.get('status')}."],
            "recommendations": [fms_analysis.get("reason") or ""],
            "needs_hints": fms_analysis.get("needs") or [],
        }
        findings.extend(battery_results["fms"]["findings"])
        if fms_analysis.get("reason"):
            recommendations.append(fms_analysis["reason"])

    for battery_id in selected:
        if battery_id == "fms":
            continue
        data = batteries.get(battery_id) or {}
        if not data:
            continue
        result = _score_non_fms(battery_id, data, ctx)
        battery_results[battery_id] = result
        findings.extend(result.get("findings") or [])
        recommendations.extend(result.get("recommendations") or [])
        extra_needs.extend(result.get("needs_hints") or [])

    if fms_analysis:
        analysis = dict(fms_analysis)
        needs = list(analysis.get("needs") or [])
        for n in extra_needs:
            if n == "breathing":
                continue
            if n == "endurance":
                if "pattern" not in needs and "strength" not in needs:
                    needs.append("strength")
                continue
            if n not in needs:
                needs.append(n)
        analysis["needs"] = needs
    else:
        needs = []
        for n in extra_needs:
            mapped = {"endurance": "strength", "breathing": "strength"}.get(n, n)
            if mapped not in needs:
                needs.append(mapped)
        if not needs:
            needs = ["strength"]
        status, target_level, reason = _status_without_fms(battery_results, needs)
        # Synthetic FMS-neutral scores so prescription templates still work
        effective = {k: 2 for k in TEST_KEYS}
        analysis = {
            "effective_scores": effective,
            "side_scores": {},
            "faults": [],
            "needs": needs,
            "total_score": sum(effective.values()),
            "status": status,
            "target_level": target_level,
            "reason": reason,
            "comments": {},
        }
        findings.insert(0, reason)
        recommendations.append(reason)

    # Deduplicate findings/recommendations preserving order
    def _uniq(items):
        seen = set()
        out = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    analysis["battery_results"] = battery_results
    analysis["selected_batteries"] = selected
    analysis["findings"] = _uniq(findings)
    analysis["recommendations"] = _uniq(recommendations)
    analysis["assessment_kind"] = "baseline_session"
    analysis["session"] = {
        "selected_batteries": selected,
        "session_notes": session.get("session_notes") or "",
    }
    # Preserve comments from FMS nested profile
    if fms_analysis and not analysis.get("comments"):
        analysis["comments"] = fms_analysis.get("comments") or {}
    return analysis


# Backward-compatible alias used by callers that previously only did FMS
def analyze_profile(payload: dict, use_manual_scores: bool = False, athlete_context: Optional[dict] = None) -> dict:
    return analyze_assessment_session(
        payload,
        use_manual_scores=use_manual_scores,
        athlete_context=athlete_context,
    )
