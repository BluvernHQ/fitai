"""Typed movement needs and comment extraction. RAG must not invent needs."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Optional

from src.logic.fms_spec import is_fault_observation, observation_polarity
from src.taxonomy import FAULT_TO_TAG_MAP

TEST_TO_PATTERN = {
    "overhead_squat": "squat",
    "hurdle_step": "lunge",
    "inline_lunge": "lunge",
    "shoulder_mobility": "push",
    "active_straight_leg_raise": "hinge",
    "trunk_stability_pushup": "push",
    "rotary_stability": "rotation",
}

TEST_TO_REGION = {
    "overhead_squat": "ankle_hip_torso",
    "hurdle_step": "hip_pelvis",
    "inline_lunge": "split_stance",
    "shoulder_mobility": "shoulder",
    "active_straight_leg_raise": "posterior_chain",
    "trunk_stability_pushup": "core",
    "rotary_stability": "rotary_core",
}

NEGATION_WINDOW = re.compile(
    r"\b(no|not|never|without|didn't|did not|doesn't|does not|n't)\b",
    re.I,
)
LEFT_RE = re.compile(r"\b(left|l-side|l side|\bl\b)\b", re.I)
RIGHT_RE = re.compile(r"\b(right|r-side|r side|\br\b)\b", re.I)
COMMENT_TAG_RULES = {
    "dorsiflexion": "fix_heels_lift",
    "heels lift": "fix_heels_lift",
    "heel lift": "fix_heels_lift",
    "ankle": "fix_heels_lift",
    "valgus": "fix_knee_valgus",
    "knee cave": "fix_knee_valgus",
    "forward lean": "fix_forward_lean",
    "pain": "stop",
    "asymmetr": "fix_asymmetry",
    "rib flare": "fix_rib_flare",
    "winging": "pattern_shoulder",
}


@dataclass
class MovementNeed:
    id: str
    source_test: str
    side: Optional[str]
    region: str
    pattern: str
    severity: int
    polarity: str
    tag: str
    confidence: float
    rule_id: str
    evidence: str
    fault: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Restriction:
    kind: str
    rule_id: str
    evidence: str
    blocks: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _keyword_negated(text: str, keyword: str) -> bool:
    clauses = re.split(r"[,.;]| but | and ", text, flags=re.I)
    for clause in clauses:
        if keyword.lower() not in clause.lower():
            continue
        idx = clause.lower().find(keyword.lower())
        prefix = clause[:idx]
        if NEGATION_WINDOW.search(prefix[-18:]):
            return True
    return False


def parse_comment_needs(comments: dict) -> list[MovementNeed]:
    needs: list[MovementNeed] = []
    for test, raw in (comments or {}).items():
        text = str(raw or "").strip()
        if not text:
            continue
        side = None
        if LEFT_RE.search(text) and not RIGHT_RE.search(text):
            side = "left"
        elif RIGHT_RE.search(text) and not LEFT_RE.search(text):
            side = "right"
        elif LEFT_RE.search(text) and RIGHT_RE.search(text):
            side = "bilateral"
        for keyword, tag in COMMENT_TAG_RULES.items():
            if keyword not in text.lower():
                continue
            if _keyword_negated(text, keyword):
                continue
            polarity = "pain" if tag == "stop" else "fault"
            needs.append(
                MovementNeed(
                    id=f"comment:{test}:{tag}",
                    source_test=test,
                    side=side,
                    region=TEST_TO_REGION.get(test, "general"),
                    pattern=TEST_TO_PATTERN.get(test, "core"),
                    severity=3 if tag == "stop" else 2,
                    polarity=polarity,
                    tag=tag,
                    confidence=0.7,
                    rule_id="comment_nlp.v1",
                    evidence=text[:180],
                    fault=keyword.replace(" ", "_"),
                )
            )
    return needs


def needs_from_analysis(analysis: dict) -> list[MovementNeed]:
    needs: list[MovementNeed] = []
    scores = analysis.get("effective_scores") or {}
    for fault in analysis.get("faults") or []:
        name = fault.get("fault") or ""
        if not name or not is_fault_observation(name) and name != "clearing_pain":
            if name != "clearing_pain" and observation_polarity(name) == "quality":
                continue
        test = fault.get("test") or "unknown"
        tag = FAULT_TO_TAG_MAP.get(name) or (
            "stop" if name in {"clearing_pain", "pain_reported"} else f"fix_{name}"
        )
        polarity = "pain" if tag == "stop" or name in {"clearing_pain", "pain_reported"} else "fault"
        severity = int(fault.get("severity") or (3 if polarity == "pain" else 2))
        needs.append(
            MovementNeed(
                id=f"obs:{test}:{name}",
                source_test=test,
                side=fault.get("side"),
                region=TEST_TO_REGION.get(test, "general"),
                pattern=TEST_TO_PATTERN.get(test, "core"),
                severity=severity,
                polarity=polarity,
                tag=tag,
                confidence=0.9 if polarity == "pain" else 0.85,
                rule_id="fms_observation.v1",
                evidence=fault.get("comment") or name.replace("_", " "),
                fault=name,
            )
        )
    for test, score in scores.items():
        if score is None:
            continue
        if score == 0:
            needs.append(
                MovementNeed(
                    id=f"score:{test}:pain",
                    source_test=test,
                    side=None,
                    region=TEST_TO_REGION.get(test, "general"),
                    pattern=TEST_TO_PATTERN.get(test, "core"),
                    severity=3,
                    polarity="pain",
                    tag="stop",
                    confidence=1.0,
                    rule_id="fms_score.v1",
                    evidence=f"{test} scored 0 (pain)",
                    fault="score_0",
                )
            )
        elif score <= 1:
            needs.append(
                MovementNeed(
                    id=f"score:{test}:low",
                    source_test=test,
                    side=None,
                    region=TEST_TO_REGION.get(test, "general"),
                    pattern=TEST_TO_PATTERN.get(test, "core"),
                    severity=2,
                    polarity="fault",
                    tag=FAULT_TO_TAG_MAP.get(test, f"pattern_{TEST_TO_PATTERN.get(test, 'core')}"),
                    confidence=0.8,
                    rule_id="fms_score.v1",
                    evidence=f"{test} scored {score}",
                    fault="low_score",
                )
            )
    needs.extend(parse_comment_needs(analysis.get("comments") or {}))
    seen = set()
    unique = []
    for need in needs:
        if need.id in seen:
            continue
        seen.add(need.id)
        unique.append(need)
    return unique


def restrictions_from_needs(needs: list[MovementNeed], analysis: dict) -> list[Restriction]:
    status = analysis.get("status")
    restrictions: list[Restriction] = []
    if status == "STOP" or any(n.polarity == "pain" or n.tag == "stop" for n in needs):
        restrictions.append(
            Restriction(
                kind="pain",
                rule_id="safety.pain_stop",
                evidence="Pain or score 0 — no loaded progression",
                blocks=["loaded_main", "plyo", "speed"],
            )
        )
    if status in {"MOBILITY", "STABILITY", "STOP"}:
        restrictions.append(
            Restriction(
                kind="level",
                rule_id="safety.no_power_early",
                evidence=f"{status} status blocks plyo/speed",
                blocks=["plyo", "speed"],
            )
        )
    if any(n.fault in {"heels_lift", "heel_lift"} or n.tag == "fix_heels_lift" for n in needs):
        restrictions.append(
            Restriction(
                kind="contraindication",
                rule_id="safety.heels_lift_no_plyo",
                evidence="Heels lift — no high-impact plyo without clearance",
                blocks=["plyo", "speed", "high_impact", "jump"],
            )
        )
    scores = analysis.get("effective_scores") or {}
    overhead_faults = {
        "arms_fall_forward",
        "shoulder_mobility_restriction_suspected",
        "bar_drifts_forward",
        "clearing_pain",
    }
    if scores.get("shoulder_mobility", 3) <= 1 or any(n.fault in overhead_faults for n in needs):
        restrictions.append(
            Restriction(
                kind="contraindication",
                rule_id="safety.no_overhead",
                evidence="Shoulder / overhead squat screen is not cleared for overhead loading",
                blocks=["overhead"],
            )
        )
    return restrictions


def build_need_bundle(analysis: dict) -> dict:
    needs = needs_from_analysis(analysis)
    restrictions = restrictions_from_needs(needs, analysis)
    return {
        "needs": [n.as_dict() for n in needs],
        "restrictions": [r.as_dict() for r in restrictions],
        "search_tags": sorted({n.tag for n in needs if n.tag}),
    }
