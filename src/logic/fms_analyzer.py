# fms_analyzer.py: Adjusted for binary inputs (0/1 present/absent). Added STOP for pain/score=0.

def analyze_fms_profile(profile, use_manual_scores=False):
    """
    Input: The full nested FMS profile dictionary.
    Output: Automatic scoring based on sub-inputs (faults) and Traffic Light logic.
    """

    # --- 1. HELPER: AUTOMATIC CALCULATOR ---
    def calculate_score_from_faults(test_name, test_data):
        """
        Returns the strictly calculated score (0-3) based on FMS decision trees from the book.
        Adjusted for binary (0=absent, 1=present for faults; reverse for positives).
        """
        # 1. Extract sub-dictionaries (ignore the manual 'score' field)
        sub_data = {k: v for k, v in test_data.items() if k != 'score'}

        # 2. Check for PAIN first (Global Override for this test)
        pain_data = sub_data.get('pain', {})
        # If pain reported > 0, score is immediately 0
        if pain_data.get('pain_reported', 0) > 0:
            return 0
        # Also check clearing_pain for relevant tests
        if test_data.get('clearing_pain', False):
            return 0

        # 3. Test-specific logic from PDF (binary-adjusted)
        if test_name == 'overhead_squat':
            feet = sub_data.get('feet', {})
            trunk = sub_data.get('trunk_torso', {})
            lower = sub_data.get('lower_limb', {})
            upper = sub_data.get('upper_body_bar_position', {})
            
            # Score 1: Major faults present (bad >0 or good ==0)
            major_faults = (
                trunk.get('excessive_forward_lean', 0) > 0 or 
                trunk.get('lumbar_flexion', 0) > 0 or
                lower.get('knee_valgus', 0) > 0 or
                feet.get('heels_lift', 0) > 0 or
                upper.get('bar_drifts_forward', 0) > 0 or
                trunk.get('upright_torso', 0) == 0  # Good thing absent
            )
            if major_faults:
                return 1
            
            # Score 2: Heels lift but others ok
            if feet.get('heels_lift', 0) > 0:
                return 2
            
            # All good → 3
            return 3

        elif test_name == 'hurdle_step':
            pelvis = sub_data.get('pelvis_core_control', {})
            stepping = sub_data.get('stepping_leg', {})
            stance = sub_data.get('stance_leg', {})
            
            # Score 1: Contact or loss of balance
            if stepping.get('toe_drag', 0) > 0 or pelvis.get('loss_of_balance', 0) > 0:
                return 1
            
            # Score 2: Alignment lost, movement in lumbar, etc.
            if (pelvis.get('excessive_rotation', 0) > 0 or 
                stance.get('knee_valgus', 0) > 0 or
                stance.get('knee_varus', 0) > 0 or
                stance.get('knee_stable', 0) == 0):
                return 2
            
            # All aligned → 3
            return 3

        elif test_name == 'inline_lunge':
            alignment = sub_data.get('alignment', {})
            lower = sub_data.get('lower_body_control', {})
            balance = sub_data.get('balance_stability', {})
            
            # Score 1: Loss of balance
            if balance.get('loss_of_balance', 0) > 0:
                return 1
            
            # Score 2: Forward lean, valgus, etc.
            if (alignment.get('excessive_forward_lean', 0) > 0 or 
                alignment.get('lateral_shift', 0) > 0 or 
                lower.get('knee_valgus', 0) > 0 or
                lower.get('heel_lift', 0) > 0 or
                lower.get('knee_tracks_over_foot', 0) == 0):
                return 2
            
            # All good → 3
            return 3

        elif test_name == 'shoulder_mobility':
            reach = sub_data.get('reach_quality', {})
            compensation = sub_data.get('compensation', {})
            
            # Score 0 already handled by pain
            # Score 1: Excessive gap or asymmetry
            if reach.get('excessive_gap', 0) > 0 or reach.get('asymmetry_present', 0) > 0:
                return 1
            
            # Score 2: Within hand length but compensation
            if compensation.get('rib_flare', 0) > 0 or compensation.get('scapular_winging', 0) > 0:
                return 2
            
            # Score 3: Within fist, no comp
            if reach.get('hands_within_fist_distance', 0) > 0:
                return 3
            return 2  # Default if partial

        elif test_name == 'active_straight_leg_raise':
            non_moving = sub_data.get('non_moving_leg', {})
            moving = sub_data.get('moving_leg', {})
            pelvic = sub_data.get('pelvic_control', {})
            
            # Score 1: <60 flexion or major faults
            if moving.get('lt_60_hip_flexion', 0) > 0 or non_moving.get('foot_lifts_off_floor', 0) > 0:
                return 1
            
            # Score 2: 60-80 with some tilt
            if pelvic.get('anterior_tilt', 0) > 0 or moving.get('hamstring_restriction', 0) > 0:
                return 2
            
            # Score 3: >80, stable
            if moving.get('gt_80_hip_flexion', 0) > 0 and pelvic.get('pelvis_stable', 0) > 0:
                return 3
            return 2

        elif test_name == 'trunk_stability_pushup':
            core = sub_data.get('core_control', {})
            body = sub_data.get('body_alignment', {})
            upper = sub_data.get('upper_body', {})
            
            # Score 1: Unable (lag or sagging)
            if core.get('hips_lag', 0) > 0 or body.get('sagging_hips', 0) > 0:
                return 1
            
            # Score 2: Minor issues
            if upper.get('uneven_arm_push', 0) > 0 or upper.get('shoulder_instability', 0) > 0:
                return 2
            
            return 3

        elif test_name == 'rotary_stability':
            diagonal = sub_data.get('diagonal_pattern', {})
            spinal = sub_data.get('spinal_control', {})
            
            # Score 1: Unable
            if diagonal.get('unable_to_complete', 0) > 0:
                return 1
            
            # Score 2: Can do with loss
            if diagonal.get('loss_of_balance', 0) > 0 or spinal.get('excessive_rotation', 0) > 0:
                return 2
            
            # Score 3: Smooth
            if diagonal.get('smooth_controlled', 0) > 0:
                return 3
            return 1
        
        # Default for any missed test
        return 3

    # --- 2. EXECUTE SCORING ---
    effective_scores = {}
    
    for test_name in profile:
        if test_name in ['use_manual_scores']: continue # Skip flag
        
        test_data = profile[test_name]
        
        # Check if sub-data exists (did the user expand and check boxes?)
        # We check this by seeing if any value in the nested dicts is > 0
        has_sub_inputs = False
        for k, v in test_data.items():
            if isinstance(v, dict):
                if sum(v.values()) > 0:
                    has_sub_inputs = True
                    break
        
        if use_manual_scores:
            # Coach override: Always use manual score
            effective_scores[test_name] = test_data.get('score', 2)
        elif has_sub_inputs:
            # AUTOMATIC MODE: Calculate based on checkboxes
            effective_scores[test_name] = calculate_score_from_faults(test_name, test_data)
        else:
            # No override, no sub-inputs: Use manual score
            effective_scores[test_name] = test_data.get('score', 2)

    # --- 3. TRAFFIC LIGHT LOGIC (With STOP for pain/0 scores) ---
    # Now we use 'effective_scores' which contains the computed values
   
    # STOP: If any score ==0 (pain)
    if any(score == 0 for score in effective_scores.values()):
        return {"status": "STOP", "target_level": 0, "reason": "Pain detected (Score 0 in one or more tests). Refer to medical professional.", "effective_scores": effective_scores}

    # RED LIGHT (Mobility)
    if effective_scores.get('active_straight_leg_raise', 3) <= 1 or \
       effective_scores.get('shoulder_mobility', 3) <= 1:
        return {"status": "MOBILITY", "target_level": 1, "reason": "Mobility Restriction (Score 1 in ASLR or SM)", "effective_scores": effective_scores}
    # YELLOW LIGHT (Stability)
    if effective_scores.get('rotary_stability', 3) <= 1 or \
       effective_scores.get('trunk_stability_pushup', 3) <= 1:
        return {"status": "STABILITY", "target_level": 3, "reason": "Motor Control Failure (Score 1 in TS or RS)", "effective_scores": effective_scores}
    # GREEN LIGHT
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