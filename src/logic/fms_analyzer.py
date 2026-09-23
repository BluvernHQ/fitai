# fms_analyzer.py: official-ish FMS scoring + traffic-light needs.

from src.logic.fms_spec import is_fault_observation, observation_polarity

TEST_KEYS = [
    "overhead_squat",
    "hurdle_step",
    "inline_lunge",
    "shoulder_mobility",
    "active_straight_leg_raise",
    "trunk_stability_pushup",
    "rotary_stability",
]

ASYMMETRICAL_TESTS = {
    "hurdle_step",
    "inline_lunge",
    "shoulder_mobility",
    "active_straight_leg_raise",
    "rotary_stability",
}

META_KEYS = {
    "score",
    "l_score",
    "r_score",
    "comment",
    "left_comment",
    "right_comment",
    "clearing_pain",
    "pain",
    "left",
    "right",
    "use_manual_scores",
}


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _score_or_none(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _has_side_nests(test_data: dict) -> bool:
    return isinstance(test_data.get("left"), dict) and isinstance(test_data.get("right"), dict)


def _side_bundle(test_data: dict, side: str) -> dict:
    nest = test_data.get(side) if isinstance(test_data.get(side), dict) else {}
    bundle = dict(nest)
    if "clearing_pain" in test_data:
        bundle["clearing_pain"] = test_data.get("clearing_pain")
    if "pain" in test_data:
        bundle["pain"] = test_data.get("pain")
    return bundle


def _official_score(test_data: dict, calculated: int) -> int:
    """FMS uses the lower of L/R when both sides are scored. None = not assessed."""
    sides = []
    for key in ("l_score", "r_score"):
        scored = _score_or_none(test_data.get(key))
        if scored is None:
            continue
        sides.append(scored)
    if not sides:
        return calculated
    return min(sides + [calculated])


def _has_fault_inputs(test_data: dict) -> bool:
    if test_data.get("clearing_pain"):
        return True
    pain = test_data.get("pain")
    if pain is True:
        return True
    if isinstance(pain, dict) and _as_int(pain.get("pain_reported")) > 0:
        return True
    for key, value in test_data.items():
        if key in META_KEYS:
            continue
        if isinstance(value, dict):
            for name, severity in value.items():
                if isinstance(severity, dict):
                    continue
                if _as_int(severity) > 0 and is_fault_observation(str(name)):
                    return True
    return False


def _has_quality_inputs(test_data: dict) -> bool:
    for key, value in test_data.items():
        if key in META_KEYS:
            continue
        if isinstance(value, dict):
            for name, severity in value.items():
                if isinstance(severity, dict):
                    continue
                if _as_int(severity) > 0 and observation_polarity(str(name)) == "quality":
                    return True
    return False


def calculate_score_from_faults(test_name, test_data):
    sub_data = {
        k: v
        for k, v in test_data.items()
        if k not in {"score", "l_score", "r_score", "comment", "left_comment", "right_comment", "left", "right"}
    }

    pain_data = sub_data.get("pain", {}) if isinstance(sub_data.get("pain"), dict) else {}
    if _as_int(pain_data.get("pain_reported", 0)) > 0:
        return 0
    if test_data.get("clearing_pain", False) or test_data.get("pain") is True:
        return 0

    if test_name == "overhead_squat":
        feet = sub_data.get("feet", {})
        trunk = sub_data.get("trunk_torso", {})
        lower = sub_data.get("lower_limb", {})
        upper = sub_data.get("upper_body_bar_position", {})

        major_faults = (
            _as_int(trunk.get("excessive_forward_lean")) > 0
            or _as_int(trunk.get("lumbar_flexion")) > 0
            or _as_int(lower.get("knee_valgus")) > 0
            or _as_int(upper.get("bar_drifts_forward")) > 0
            or _as_int(trunk.get("lumbar_extension_sway_back")) > 0
        )
        if major_faults:
            return 1
        if _as_int(feet.get("heels_lift")) > 0:
            return 2
        if _as_int(trunk.get("upright_torso"), 1) == 0:
            return 2
        return 3

    if test_name == "hurdle_step":
        pelvis = sub_data.get("pelvis_core_control", {})
        stepping = sub_data.get("stepping_leg", {})
        stance = sub_data.get("stance_leg", {})
        if _as_int(stepping.get("toe_drag")) > 0 or _as_int(pelvis.get("loss_of_balance")) > 0:
            return 1
        if (
            _as_int(pelvis.get("excessive_rotation")) > 0
            or _as_int(stance.get("knee_valgus")) > 0
            or _as_int(stance.get("knee_varus")) > 0
        ):
            return 2
        return 3

    if test_name == "inline_lunge":
        alignment = sub_data.get("alignment", {})
        lower = sub_data.get("lower_body_control", {})
        balance = sub_data.get("balance_stability", {})
        if _as_int(balance.get("loss_of_balance")) > 0:
            return 1
        if (
            _as_int(alignment.get("excessive_forward_lean")) > 0
            or _as_int(alignment.get("lateral_shift")) > 0
            or _as_int(lower.get("knee_valgus")) > 0
            or _as_int(lower.get("heel_lift")) > 0
        ):
            return 2
        return 3

    if test_name == "shoulder_mobility":
        reach = sub_data.get("reach_quality", {})
        compensation = sub_data.get("compensation", {})
        if _as_int(reach.get("excessive_gap")) > 0 or _as_int(reach.get("asymmetry_present")) > 0:
            return 1
        if _as_int(compensation.get("rib_flare")) > 0 or _as_int(compensation.get("scapular_winging")) > 0:
            return 2
        if _as_int(reach.get("hands_within_fist_distance")) > 0:
            return 3
        return 2

    if test_name == "active_straight_leg_raise":
        non_moving = sub_data.get("non_moving_leg", {})
        moving = sub_data.get("moving_leg", {})
        pelvic = sub_data.get("pelvic_control", {})
        if _as_int(moving.get("lt_60_hip_flexion")) > 0 or _as_int(non_moving.get("foot_lifts_off_floor")) > 0:
            return 1
        if _as_int(pelvic.get("anterior_tilt")) > 0 or _as_int(moving.get("hamstring_restriction")) > 0:
            return 2
        if _as_int(moving.get("gt_80_hip_flexion")) > 0:
            return 3
        return 2

    if test_name == "trunk_stability_pushup":
        core = sub_data.get("core_control", {})
        body = sub_data.get("body_alignment", {})
        upper = sub_data.get("upper_body", {})
        if _as_int(core.get("hips_lag")) > 0 or _as_int(body.get("sagging_hips")) > 0:
            return 1
        if _as_int(upper.get("uneven_arm_push")) > 0 or _as_int(upper.get("shoulder_instability")) > 0:
            return 2
        return 3

    if test_name == "rotary_stability":
        diagonal = sub_data.get("diagonal_pattern", {})
        spinal = sub_data.get("spinal_control", {})
        if _as_int(diagonal.get("unable_to_complete")) > 0:
            return 1
        if _as_int(diagonal.get("loss_of_balance")) > 0 or _as_int(spinal.get("excessive_rotation")) > 0:
            return 2
        if _as_int(diagonal.get("smooth_controlled")) > 0:
            return 3
        return 2

    return 3


def _score_one_side(test_name: str, side_data: dict, use_manual: bool, raw_side_score):
    """Return 0–3, or None when the side has no observations / coach score yet."""
    pain = bool(side_data.get("clearing_pain")) or side_data.get("pain") is True
    if isinstance(side_data.get("pain"), dict) and _as_int(side_data["pain"].get("pain_reported")) > 0:
        pain = True
    if pain:
        return 0
    has_faults = _has_fault_inputs(side_data)
    from_obs = calculate_score_from_faults(test_name, side_data) if has_faults else None
    if from_obs is None and _has_quality_inputs(side_data):
        from_obs = 3
    from_coach = _score_or_none(raw_side_score) if use_manual else None
    if from_obs is not None and from_coach is not None:
        return min(from_coach, from_obs)
    if from_obs is not None:
        return from_obs
    if from_coach is not None:
        return from_coach
    return None


def _collect_faults_from_sections(test_name: str, sections: dict, comment: str, side) -> list[dict]:
    faults = []
    for category, details in (sections or {}).items():
        if category in META_KEYS or not isinstance(details, dict):
            continue
        for fault_name, severity in details.items():
            if isinstance(severity, dict):
                continue
            if _as_int(severity) <= 0:
                continue
            if not is_fault_observation(str(fault_name)):
                continue
            faults.append(
                {
                    "test": test_name,
                    "fault": fault_name,
                    "severity": _as_int(severity),
                    "comment": comment,
                    "polarity": "pain" if fault_name in {"pain_reported"} else "fault",
                    "side": side,
                }
            )
    return faults


def _collect_faults(profile: dict) -> list[dict]:
    faults = []
    for test_name, test_data in profile.items():
        if test_name in {"use_manual_scores", "student_id"} or not isinstance(test_data, dict):
            continue
        comment = test_data.get("comment") or ""
        if test_data.get("clearing_pain") or test_data.get("pain") is True:
            faults.append(
                {"test": test_name, "fault": "clearing_pain", "comment": comment, "polarity": "pain", "side": None}
            )
        if _has_side_nests(test_data):
            left_comment = test_data.get("left_comment") or comment
            right_comment = test_data.get("right_comment") or comment
            faults.extend(_collect_faults_from_sections(test_name, test_data.get("left"), left_comment, "left"))
            faults.extend(_collect_faults_from_sections(test_name, test_data.get("right"), right_comment, "right"))
        else:
            faults.extend(_collect_faults_from_sections(test_name, test_data, comment, None))
    return faults


def _needs_from_scores(effective_scores: dict, faults: list[dict], side_scores=None) -> list[str]:
    needs = []
    if any(score == 0 for score in effective_scores.values()):
        needs.append("pain-stop")
    if effective_scores.get("active_straight_leg_raise", 3) <= 1 or effective_scores.get("shoulder_mobility", 3) <= 1:
        needs.append("mobility")
    if effective_scores.get("rotary_stability", 3) <= 1 or effective_scores.get("trunk_stability_pushup", 3) <= 1:
        needs.append("stability")
    min_pattern = min(
        effective_scores.get("hurdle_step", 3),
        effective_scores.get("inline_lunge", 3),
        effective_scores.get("overhead_squat", 3),
    )
    if min_pattern <= 2:
        needs.append("pattern")
    asymmetric = any(
        f["fault"] in {"asymmetry_present", "uneven_depth", "left_side_deficit", "right_side_deficit"} for f in faults
    )
    if side_scores:
        for sides in side_scores.values():
            if sides.get("l") is not None and sides.get("r") is not None and sides["l"] != sides["r"]:
                asymmetric = True
                break
    if asymmetric:
        needs.append("asymmetry")
    if not needs:
        needs.append("strength")
    return needs


def analyze_fms_profile(profile, use_manual_scores=False):
    if not isinstance(profile, dict):
        profile = {}

    use_manual = use_manual_scores or profile.get("use_manual_scores", False)
    effective_scores = {}
    side_scores: dict[str, dict] = {}

    for test_name in TEST_KEYS:
        test_data = profile.get(test_name, {})
        if not isinstance(test_data, dict):
            test_data = {"score": _score_or_none(test_data) if test_data not in (None, "") else None}

        pain = bool(test_data.get("clearing_pain")) or test_data.get("pain") is True

        if pain:
            calculated = 0
            l_score = 0
            r_score = 0
        elif _has_side_nests(test_data) and test_name in ASYMMETRICAL_TESTS:
            left = _side_bundle(test_data, "left")
            right = _side_bundle(test_data, "right")
            l_score = _score_one_side(test_name, left, use_manual, test_data.get("l_score"))
            r_score = _score_one_side(test_name, right, use_manual, test_data.get("r_score"))
            if l_score is None or r_score is None:
                calculated = None
            else:
                calculated = min(l_score, r_score)
            test_data = {**test_data, "l_score": l_score, "r_score": r_score}
            side_scores[test_name] = {"l": l_score, "r": r_score}
        else:
            has_faults = _has_fault_inputs(test_data)
            raw_score = _score_or_none(test_data.get("score")) if use_manual else None
            from_obs = calculate_score_from_faults(test_name, test_data) if has_faults else None
            if from_obs is None and _has_quality_inputs(test_data):
                from_obs = 3
            from_coach = raw_score
            if from_obs is not None and from_coach is not None:
                calculated = min(from_coach, from_obs)
            elif from_obs is not None:
                calculated = from_obs
            elif from_coach is not None:
                calculated = from_coach
            else:
                calculated = None
            l_score = _score_or_none(test_data.get("l_score"))
            r_score = _score_or_none(test_data.get("r_score"))
            if l_score is not None or r_score is not None:
                side_scores[test_name] = {"l": l_score, "r": r_score}

        if calculated is None:
            effective_scores[test_name] = None
        else:
            effective_scores[test_name] = _official_score(test_data, calculated)

    faults = _collect_faults(profile)
    incomplete = [k for k, v in effective_scores.items() if v is None]
    # For needs / status, treat incomplete screens as unscored pattern risk (not as filled 2s)
    scored_only = {k: v for k, v in effective_scores.items() if v is not None}
    needs = _needs_from_scores(
        {**{k: 2 for k in incomplete}, **scored_only} if incomplete else effective_scores,
        faults,
        side_scores,
    )
    if incomplete:
        needs = [n for n in needs if n != "strength"]
        if "pattern" not in needs:
            needs.append("pattern")
    total_score = sum(v for v in effective_scores.values() if v is not None)

    def _s(key, default=3):
        v = effective_scores.get(key)
        return default if v is None else v

    if "pain-stop" in needs or any(score == 0 for score in scored_only.values()):
        status, target_level, reason = (
            "STOP",
            0,
            "Pain detected (Score 0). Refer to a medical professional before loading.",
        )
    elif incomplete:
        status, target_level, reason = (
            "PATTERN",
            5,
            f"Incomplete screen(s): {', '.join(incomplete)}. Score both sides / mark observations before trusting status.",
        )
    elif "mobility" in needs:
        status, target_level, reason = "MOBILITY", 1, "Mobility restriction (ASLR or Shoulder Mobility ≤ 1)."
    elif "stability" in needs:
        status, target_level, reason = "STABILITY", 3, "Motor control limitation (Trunk or Rotary ≤ 1)."
    elif _s("overhead_squat") <= 1 or min(_s("hurdle_step"), _s("inline_lunge"), _s("overhead_squat")) <= 1:
        status, target_level, reason = "PATTERN", 5, "Pattern dysfunction (Squat/Hurdle/Lunge ≤ 1)."
    elif min(_s("hurdle_step"), _s("inline_lunge"), _s("overhead_squat")) == 2:
        status, target_level, reason = "STRENGTH", 7, "Acceptable patterning. Cleared for strength."
    else:
        status, target_level, reason = "POWER", 9, "Strong patterning. Cleared for power."

    comments = {}
    for test in TEST_KEYS:
        row = profile.get(test) or {}
        if not isinstance(row, dict):
            continue
        parts = []
        if row.get("comment"):
            parts.append(str(row["comment"]))
        if row.get("left_comment"):
            parts.append(f"L: {row['left_comment']}")
        if row.get("right_comment"):
            parts.append(f"R: {row['right_comment']}")
        if parts:
            comments[test] = " | ".join(parts)

    return {
        "effective_scores": effective_scores,
        "side_scores": side_scores,
        "faults": faults,
        "needs": needs,
        "total_score": total_score,
        "status": status,
        "target_level": target_level,
        "reason": reason,
        "comments": comments,
        "incomplete_screens": incomplete,
        "detailed_faults": profile,
    }
