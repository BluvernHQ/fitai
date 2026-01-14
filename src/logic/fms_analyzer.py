def analyze_fms_profile(scores):
    """
    Input: A dictionary of 7 FMS scores.
    Output: The specific 'Squat Level' (1-10) the athlete is cleared for.
    """
    
    # -----------------------------------------------------------
    # 1. SAFETY STOP - MASTER SWITCH
    # We ONLY stop if the explicit 'pain_present' flag is True.
    # We ignore 0s in the scores here, assuming 0 means "Total Failure" if pain is false.
    # -----------------------------------------------------------
    if scores.get('pain_present') is True:
        return {
            "status": "STOP",
            "target_level": 0,
            "reason": "Pain reported by user. Medical referral required."
        }

    # -----------------------------------------------------------
    # 2. RED LIGHT: MOBILITY (ASLR & Shoulder)
    # Check if Score is 1 OR 0 (Severe Dysfunction).
    # -----------------------------------------------------------
    aslr = scores.get('active_straight_leg_raise', 3)
    shoulder = scores.get('shoulder_mobility', 3)

    if aslr <= 1 or shoulder <= 1:
        return {
            "status": "MOBILITY",
            "target_level": 1,
            "reason": "Mobility restriction detected (ASLR or Shoulder <= 1). Reverting to Level 1 Correctives."
        }

    # -----------------------------------------------------------
    # 3. YELLOW LIGHT: MOTOR CONTROL (Rotary & Trunk)
    # Check if Score is 1 OR 0.
    # -----------------------------------------------------------
    rotary = scores.get('rotary_stability', 3)
    trunk = scores.get('trunk_stability_pushup', 3)

    if rotary <= 1 or trunk <= 1:
        return {
            "status": "STABILITY",
            "target_level": 3, 
            "reason": "Core Stability restriction detected. Reverting to Level 3 Static/Stability work."
        }

    # -----------------------------------------------------------
    # 4. GREEN LIGHT: SQUAT PATTERN
    # Mobility and Core are cleared. Now look at the Squat score itself.
    # -----------------------------------------------------------
    squat_score = scores.get('deep_squat', 1)
    
    if squat_score <= 1:
        return {
            "status": "PATTERN",
            "target_level": 5,
            "reason": "Foundations cleared, but Squat pattern is dysfunctional. Target Level 5 Patterning."
        }
    elif squat_score == 2:
        return {
            "status": "STRENGTH",
            "target_level": 7,
            "reason": "Squat pattern acceptable (2). Cleared for Level 7 Loading."
        }
    elif squat_score == 3:
        return {
            "status": "POWER",
            "target_level": 9,
            "reason": "Squat pattern optimal (3). Cleared for Level 9 Performance/Power."
        }

    # Fallback
    return {"status": "ERROR", "target_level": 1, "reason": "Unknown profile."}