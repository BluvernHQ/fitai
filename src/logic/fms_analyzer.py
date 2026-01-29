def analyze_fms_profile(profile, use_manual_scores=False):
    """
    Input: Full nested FMS profile dictionary (with sub-faults 0-4).
    Output: Automatic scoring (0-3) matching official FMS criteria + traffic light logic.
    """
    # --- HELPER: AUTOMATIC CALCULATOR ---
    def calculate_score_from_faults(test_name, test_data):
        """
        Exact FMS scoring from FMSScoringCriteria.pdf.
        Returns 0-3 based on specific pass/fail conditions.
        """
        sub_data = {k: v for k, v in test_data.items() if k != 'score'}

        # Pain anywhere in test → 0
        pain_data = sub_data.get('pain', {})
        if pain_data.get('pain_reported', 0) > 0:
            return 0

        # ────────────────────────────────────────────────
        # DEEP SQUAT / OVERHEAD SQUAT
        # ────────────────────────────────────────────────
        if test_name == 'overhead_squat':
            feet = sub_data.get('feet', {})
            trunk = sub_data.get('trunk_torso', {})
            lower = sub_data.get('lower_limb', {})
            upper = sub_data.get('upper_body_bar_position', {})

            # Score 1 conditions (any one fails → 1)
            if (trunk.get('excessive_forward_lean', 0) > 1 or
                trunk.get('lumbar_flexion', 0) > 1 or
                lower.get('knees_track_over_toes', 0) < 2 or  # not aligned
                feet.get('heels_stay_down', 0) < 2 or         # femur not below horizontal
                upper.get('bar_aligned_over_mid_foot', 0) < 2 or  # dowel not aligned
                upper.get('bar_drifts_forward', 0) > 1 or
                upper.get('arms_fall_forward', 0) > 1):
                return 1

            # Score 2: Heels elevated allowed, but everything else perfect
            if feet.get('heels_lift', 0) > 0:
                return 2

            # Score 3: All perfect
            return 3

        # ────────────────────────────────────────────────
        # HURDLE STEP
        # ────────────────────────────────────────────────
        elif test_name == 'hurdle_step':
            pelvis = sub_data.get('pelvis_core_control', {})
            stepping = sub_data.get('stepping_leg', {})
            stance = sub_data.get('stance_leg', {})

            # Score 1: Contact or loss of balance
            if stepping.get('toe_drag', 0) > 0 or pelvis.get('loss_of_balance', 0) > 0:
                return 1

            # Score 2: Alignment lost or movement in lumbar
            if (pelvis.get('excessive_rotation', 0) > 0 or
                stance.get('knee_valgus', 0) > 0 or
                stance.get('knee_varus', 0) > 0 or
                stance.get('knee_stable', 0) < 2):
                return 2

            # Score 3: All aligned, no movement
            return 3

        # ────────────────────────────────────────────────
        # INLINE LUNGE
        # ────────────────────────────────────────────────
        elif test_name == 'inline_lunge':
            alignment = sub_data.get('alignment', {})
            lower = sub_data.get('lower_body_control', {})
            balance = sub_data.get('balance_stability', {})

            # Score 1: Loss of balance
            if balance.get('loss_of_balance', 0) > 0:
                return 1

            # Score 2: Dowel not vertical, torso movement, not sagittal, knee not touch
            if (alignment.get('excessive_forward_lean', 0) > 0 or
                alignment.get('lateral_shift', 0) > 0 or
                lower.get('knee_tracks_over_foot', 0) < 2 or
                lower.get('heel_lift', 0) > 0):
                return 2

            # Score 3: All perfect
            return 3

        # ────────────────────────────────────────────────
        # SHOULDER MOBILITY
        # ────────────────────────────────────────────────
        elif test_name == 'shoulder_mobility':
            reach = sub_data.get('reach_quality', {})

            # Score 3: Fists within one hand length
            if reach.get('hands_within_fist_distance', 0) > 0:
                return 3

            # Score 2: Within one-and-a-half hand lengths
            if reach.get('hands_within_hand_length', 0) > 0:
                return 2

            # Score 1: Not within 1.5
            return 1

        # ────────────────────────────────────────────────
        # ACTIVE STRAIGHT-LEG RAISE
        # ────────────────────────────────────────────────
        elif test_name == 'active_straight_leg_raise':
            moving = sub_data.get('moving_leg', {})
            non_moving = sub_data.get('non_moving_leg', {})

            # Non-moving limb not neutral → 1
            if non_moving.get('remains_flat', 0) < 2:
                return 1

            # Score 3: Malleolus > mid-thigh to ASIS
            if moving.get('gt_80_hip_flexion', 0) > 0:
                return 3

            # Score 2: Malleolus between mid-thigh and joint line
            if moving.get('between_60_80_hip_flexion', 0) > 0:
                return 2

            # Score 1: Below joint line
            return 1

        # ────────────────────────────────────────────────
        # TRUNK STABILITY PUSH-UP
        # ────────────────────────────────────────────────
        elif test_name == 'trunk_stability_pushup':
            core = sub_data.get('core_control', {})
            body = sub_data.get('body_alignment', {})

            # Score 1: Lag or sagging
            if core.get('hips_lag', 0) > 0 or body.get('sagging_hips', 0) > 0:
                return 1

            # Score 2 vs 3 depends on thumb position (men: head, women: chin) — not in data
            # Assume 3 if no major faults, 2 if minor upper body issues
            if core.get('excessive_lumbar_extension', 0) > 0:
                return 2

            return 3

        # ────────────────────────────────────────────────
        # ROTARY STABILITY
        # ────────────────────────────────────────────────
        elif test_name == 'rotary_stability':
            diagonal = sub_data.get('diagonal_pattern', {})

            # Score 1: Inability to perform diagonal
            if diagonal.get('unable_to_complete', 0) > 0:
                return 1

            # Score 2: Correct diagonal (touching back)
            if diagonal.get('smooth_controlled', 0) > 0 and diagonal.get('loss_of_balance', 0) <= 1:
                return 2

            # Score 3: Correct unilateral
            if diagonal.get('smooth_controlled', 0) > 1 and diagonal.get('loss_of_balance', 0) == 0:
                return 3

            return 1

        # Default fallback
        return 3

    # ────────────────────────────────────────────────
    # EXECUTE SCORING
    # ────────────────────────────────────────────────
    effective_scores = {}

    for test_name in profile:
        if test_name in ['use_manual_scores']: continue

        test_data = profile[test_name]

        has_sub_inputs = any(
            isinstance(v, dict) and sum(v.values()) > 0
            for v in test_data.values()
        )

        if use_manual_scores:
            effective_scores[test_name] = test_data.get('score', 2)
        elif has_sub_inputs:
            effective_scores[test_name] = calculate_score_from_faults(test_name, test_data)
        else:
            effective_scores[test_name] = test_data.get('score', 2)

    # ────────────────────────────────────────────────
    # TRAFFIC LIGHT LOGIC (unchanged)
    # ────────────────────────────────────────────────
    if effective_scores.get('active_straight_leg_raise', 3) <= 1 or \
       effective_scores.get('shoulder_mobility', 3) <= 1:
        return {"status": "MOBILITY", "target_level": 1, "reason": "Mobility Restriction (Score 1 in ASLR or SM)", "effective_scores": effective_scores}

    if effective_scores.get('rotary_stability', 3) <= 1 or \
       effective_scores.get('trunk_stability_pushup', 3) <= 1:
        return {"status": "STABILITY", "target_level": 3, "reason": "Motor Control Failure (Score 1 in TS or RS)", "effective_scores": effective_scores}

    min_pattern = min(
        effective_scores.get('hurdle_step', 3),
        effective_scores.get('inline_lunge', 3),
        effective_scores.get('overhead_squat', 3)
    )

    if min_pattern <= 1:
        return {"status": "PATTERN", "target_level": 5, "reason": "Pattern Dysfunction (Score 1 in Squat/Hurdle/Lunge)", "effective_scores": effective_scores}
    elif min_pattern == 2:
        return {"status": "STRENGTH", "target_level": 7, "reason": "Acceptable Patterning (Score 2). Cleared for Strength.", "effective_scores": effective_scores}
    else:
        return {"status": "POWER", "target_level": 9, "reason": "Perfect Patterning (Score 3). Cleared for Power.", "effective_scores": effective_scores}