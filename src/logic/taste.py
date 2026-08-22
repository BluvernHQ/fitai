"""Honest coach-taste posteriors. Taste never overrides safety."""

from __future__ import annotations

from typing import Optional

DISPLAY_ONLY_MAX = 9
RANK_MIN_EVIDENCE = 10
TASTE_CAP = 0.5


def beta_keep_estimate(shown: int, kept: int, replaced: int, alpha: float = 1.0) -> dict:
    shown = max(int(shown or 0), 0)
    kept = max(int(kept or 0), 0)
    replaced = max(int(replaced or 0), 0)
    # exposure is shown; outcomes are kept/replaced and must not inflate shown
    a = kept + alpha
    b = max(shown - kept, 0) + alpha
    mean = a / (a + b) if (a + b) else 0.5
    # Normal approximation of Beta variance for a readable band, not a fake CI product claim
    var = (a * b) / (((a + b) ** 2) * (a + b + 1)) if (a + b) > 1 else 0.25
    sd = var ** 0.5
    return {
        "shown": shown,
        "kept": kept,
        "replaced": replaced,
        "posterior_keep": round(mean, 3),
        "band": [round(max(0.0, mean - 1.96 * sd), 3), round(min(1.0, mean + 1.96 * sd), 3)],
        "sample_size": shown,
    }


def taste_label(sample_size: int, applied: bool) -> str:
    if sample_size <= 0:
        return "No coach history for this exercise yet"
    if sample_size <= DISPLAY_ONLY_MAX:
        return f"Early preference signal · {sample_size} similar decisions"
    if applied:
        return f"Based on {sample_size} similar decisions"
    return f"Based on {sample_size} similar decisions · not used in ranking"


def prior_contribution(priors: dict, exercise_id: str, ctx: str) -> dict:
    stats = (priors or {}).get(f"{exercise_id}|{ctx}") or (priors or {}).get(exercise_id) or {}
    shown = int(stats.get("shown") or 0)
    kept = int(stats.get("kept") or 0)
    replaced = int(stats.get("replaced") or 0)
    estimate = beta_keep_estimate(shown, kept, replaced)
    applied = shown >= RANK_MIN_EVIDENCE
    penalty = replaced / max(shown, 1) if shown else 0.0
    raw = (estimate["posterior_keep"] - 0.5) - 0.25 * penalty
    score = max(-TASTE_CAP, min(TASTE_CAP, raw)) if applied else 0.0
    return {
        **estimate,
        "applied": applied,
        "score": round(score, 4),
        "label": taste_label(shown, applied),
    }


def insights_payload(priors: dict, *, min_shown: int = 3) -> dict:
    rows = []
    seen = set()
    for key, stats in (priors or {}).items():
        if "|" not in str(key):
            continue
        exercise_id, ctx = str(key).split("|", 1)
        if exercise_id in seen:
            continue
        shown = int(stats.get("shown") or 0)
        if shown < min_shown:
            continue
        seen.add(exercise_id)
        contrib = prior_contribution({key: stats, exercise_id: stats}, exercise_id, ctx)
        rows.append(
            {
                "exercise_id": exercise_id,
                "context_key": ctx,
                **contrib,
            }
        )
    rows.sort(key=lambda r: (r["applied"], r["posterior_keep"], r["shown"]), reverse=True)
    return {
        "threshold": {"display_only_max": DISPLAY_ONLY_MAX, "rank_min": RANK_MIN_EVIDENCE},
        "disclaimer": "Taste never overrides safety, equipment, or level gates.",
        "preferences": rows[:40],
        "emerging": [r for r in rows if not r["applied"]][:12],
        "kept_often": [r for r in rows if r["applied"] and r["posterior_keep"] >= 0.65][:12],
        "replaced_often": [r for r in rows if r["replaced"] >= 3 and r["posterior_keep"] <= 0.4][:12],
    }


def plans_differ_selection(ai_plan: Optional[dict], coach_plan: Optional[dict]) -> bool:
    if not coach_plan or not ai_plan:
        return False
    def ids(plan: dict) -> list[str]:
        out = []
        for day in plan.get("days") or []:
            for items in (day.get("blocks") or {}).values():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if isinstance(item, dict) and item.get("exercise_id"):
                        out.append(item["exercise_id"])
        return out
    return ids(ai_plan) != ids(coach_plan)
