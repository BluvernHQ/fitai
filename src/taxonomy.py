"""Shared FMS fault → exercise tag taxonomy."""

FAULT_TO_TAG_MAP = {
    "heels_lift": "fix_heels_lift",
    "knee_valgus": "fix_knee_valgus",
    "knee_varus": "pattern_squat",
    "excessive_forward_lean": "fix_forward_lean",
    "lumbar_flexion": "fix_lumbar_flexion",
    "uneven_depth": "fix_asymmetry",
    "pelvic_drop_trendelenburg": "fix_pelvic_drop",
    "loss_of_balance": "level_1",
    "default_squat": "pattern_squat",
    "rib_flare": "fix_rib_flare",
    "lumbar_extension_sway_back": "fix_lumbar_extension",
    "excessive_pronation": "fix_heels_lift",
    "excessive_supination": "fix_heels_lift",
    "bar_drifts_forward": "fix_forward_lean",
    "arms_fall_forward": "fix_shoulder_mobility",
    "shoulder_mobility_restriction_suspected": "pattern_shoulder",
    "excessive_rotation": "fix_rotary_instability",
    "ankle_instability": "fix_heels_lift",
    "toe_drag": "pattern_step",
    "hip_flexion_restriction": "pattern_leg_raise",
    "asymmetrical_movement": "fix_asymmetry",
    "forward_head": "fix_forward_lean",
    "lateral_shift": "fix_lateral_shift",
    "knee_instability": "fix_knee_valgus",
    "heel_lift": "fix_heels_lift",
    "wobbling": "level_1",
    "unequal_weight_distribution": "fix_asymmetry",
    "excessive_gap": "pattern_shoulder",
    "asymmetry_present": "fix_asymmetry",
    "spine_flexion": "fix_lumbar_flexion",
    "scapular_winging": "pattern_shoulder",
    "knee_bends": "fix_knee_instability",
    "hip_externally_rotates": "fix_hip_rotation",
    "foot_lifts_off_floor": "fix_heels_lift",
    "lt_60_hip_flexion": "pattern_leg_raise",
    "hamstring_restriction": "pattern_leg_raise",
    "anterior_tilt": "fix_pelvic_tilt",
    "posterior_tilt": "fix_pelvic_tilt",
    "sagging_hips": "fix_core_stability",
    "pike_position": "fix_core_stability",
    "hips_lag": "fix_core_stability",
    "excessive_lumbar_extension": "fix_lumbar_extension",
    "uneven_arm_push": "fix_asymmetry",
    "shoulder_instability": "pattern_shoulder",
    "unable_to_complete": "level_1",
    "lumbar_shift": "fix_lumbar_flexion",
    "left_side_deficit": "fix_asymmetry",
    "right_side_deficit": "fix_asymmetry",
}

TAG_RULES = {
    "ankle": ["fix_heels_lift", "ankle_mobility"],
    "dorsiflexion": ["fix_heels_lift", "ankle_mobility"],
    "heel": ["fix_heels_lift"],
    "wall slide": ["fix_thoracic_stiffness", "fix_forward_lean"],
    "thoracic": ["fix_forward_lean", "thoracic_mobility"],
    "band": ["fix_knee_valgus", "rnt_correction"],
    "valgus": ["fix_knee_valgus"],
    "glute": ["fix_knee_valgus", "glute_activation"],
    "pain": ["stop"],
    "asymmetry": ["fix_asymmetry"],
    "rotation": ["fix_rotary_instability", "pattern_rotary"],
    "pelvic": ["fix_pelvic_drop", "fix_pelvic_tilt"],
    "hip": ["pattern_leg_raise", "fix_hip_rotation"],
    "shoulder": ["pattern_shoulder"],
    "scap": ["pattern_shoulder"],
    "core": ["fix_core_stability"],
    "plank": ["fix_lumbar_extension", "core_stability"],
    "deadbug": ["fix_rib_flare", "core_stability"],
    "chop": ["fix_rotary_instability", "anti_rotation"],
    "carry": ["fix_asymmetry", "stability"],
    "squat": ["pattern_squat"],
    "lunge": ["pattern_lunge"],
    "split": ["pattern_lunge", "fix_asymmetry"],
    "deadlift": ["pattern_hinge"],
    "hinge": ["pattern_hinge"],
    "bridge": ["pattern_hinge", "glute_activation"],
    "row": ["pattern_pull"],
    "pull": ["pattern_pull"],
    "press": ["pattern_push"],
    "push": ["pattern_push"],
    "march": ["pattern_step", "pattern_gait"],
    "walk": ["pattern_gait"],
    "sprint": ["pattern_speed"],
    "jump": ["pattern_plyo"],
    "landing": ["pattern_plyo"],
    "single leg": ["fix_asymmetry", "unilateral"],
    "lumbar": ["fix_lumbar_flexion", "fix_lumbar_extension"],
    "rib": ["fix_rib_flare"],
}

TYPO_FIXES = {
    "POTANTIATE": "POTENTIATE",
    "DECELARATION": "DECELERATION",
    "ACCELARATION": "ACCELERATION",
    "PRISIONER": "PRISONER",
}

CATEGORY_ALIASES = {
    "FRONT SQUATS": "FRONT RACKED SQUATS",
    "BACK SQUATS": "BACK RACKED SQUATS",
    "OH SQUATS": "OVERHEAD SQUATS",
}

SHEET_PATTERN = {
    "WARM-UP": "warmup",
    "SQUAT & LUNGE DESCRIPTIONS": "squat",
    "HINGE DESCRIPTIONS": "hinge",
    "VERTICAL PUSH DESCRIPTIONS": "push",
    "VERTICAL PULL DESCRIPTIONS": "pull",
    "HORIZONTAL PUSH DESCRIPTIONS": "push",
    "HORIZONTAL PULL DESCRIPTIONS": "pull",
    "ROTATION": "rotation",
    "CORE": "core",
    "LOCOMOTION-GAIT": "gait",
    "PLYOMETRICS - ATHLETIC POWER": "plyo",
    "SPEED - AGILITY (COD)": "speed",
}

SHEET_PROGRAM_ROLE = {
    "WARM-UP": "warmup",
    "SQUAT & LUNGE DESCRIPTIONS": "main",
    "HINGE DESCRIPTIONS": "main",
    "VERTICAL PUSH DESCRIPTIONS": "main",
    "VERTICAL PULL DESCRIPTIONS": "main",
    "HORIZONTAL PUSH DESCRIPTIONS": "main",
    "HORIZONTAL PULL DESCRIPTIONS": "main",
    "ROTATION": "accessory",
    "CORE": "accessory",
    "LOCOMOTION-GAIT": "conditioning",
    "PLYOMETRICS - ATHLETIC POWER": "power",
    "SPEED - AGILITY (COD)": "power",
}


def generate_smart_tags(name: str, family: str, pattern: str, level: int, ramp_role=None):
    tags = [
        family.lower().replace(" ", "_").replace("-", "_"),
        f"level_{level}",
        f"pattern_{pattern}" if not pattern.startswith("pattern_") else pattern,
    ]
    if ramp_role:
        tags.append(f"ramp_{ramp_role}")
    search_text = f"{name} {family} {pattern}".lower()
    for keyword, new_tags in TAG_RULES.items():
        if keyword in search_text:
            tags.extend(new_tags)
    return sorted(set(tags))
