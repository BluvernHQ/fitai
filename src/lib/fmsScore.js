/** Live FMS scoring — same rules as backend `fms_analyzer.calculate_score_from_faults`. */

export const QUALITY_KEYS = new Set([
  "upright_torso",
  "knees_track_over_toes",
  "heels_stay_down",
  "bar_aligned_over_mid_foot",
  "pelvis_stable",
  "knee_stable",
  "clears_hurdle_smoothly",
  "head_neutral",
  "trunk_upright",
  "knee_tracks_over_foot",
  "stable_throughout",
  "hands_within_fist_distance",
  "hands_within_hand_length",
  "no_compensation",
  "no_pain",
  "remains_flat",
  "gt_80_hip_flexion",
  "neutral_spine_maintained",
  "initiates_as_one_unit",
  "elbows_aligned",
  "smooth_controlled",
  "neutral_maintained",
  "symmetrical",
]);

const LEFT_RE = /\b(left|l-side|l side|\bl\b)\b/i;
const RIGHT_RE = /\b(right|r-side|r side|\br\b)\b/i;

const asInt = (value, fallback = 0) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};

export const isQualityKey = (key, specObs) => {
  if (specObs?.polarity === "quality") return true;
  if (specObs?.polarity === "fault" || specObs?.polarity === "pain") return false;
  return QUALITY_KEYS.has(key);
};

export const isFaultKey = (key, specObs) => {
  if (specObs?.polarity === "quality") return false;
  if (specObs?.polarity === "fault" || specObs?.polarity === "pain" || specObs?.polarity === "moderate") {
    return true;
  }
  return Boolean(key) && !QUALITY_KEYS.has(key);
};

const on = (section, key) => asInt(section?.[key]) > 0;

const hasFaultInputs = (data = {}) => {
  if (data.clearing_pain || data.pain === true) return true;
  for (const [key, value] of Object.entries(data)) {
    if (["score", "l_score", "r_score", "comment", "clearing_pain", "pain"].includes(key)) continue;
    if (!value || typeof value !== "object") continue;
    for (const [name, severity] of Object.entries(value)) {
      if (asInt(severity) > 0 && isFaultKey(name)) return true;
    }
  }
  return false;
};

const hasQualityInputs = (data = {}) => {
  for (const [key, value] of Object.entries(data)) {
    if (typeof value !== "object" || !value) continue;
    for (const [name, severity] of Object.entries(value)) {
      if (asInt(severity) > 0 && isQualityKey(name)) return true;
    }
  }
  return false;
};

export const calculateScoreFromFaults = (testName, data = {}) => {
  const pain = data.pain || {};
  if (on(pain, "pain_reported") || data.clearing_pain || data.pain === true) return 0;

  if (testName === "overhead_squat") {
    const feet = data.feet || {};
    const trunk = data.trunk_torso || {};
    const lower = data.lower_limb || {};
    const upper = data.upper_body_bar_position || {};
    const major =
      on(trunk, "excessive_forward_lean") ||
      on(trunk, "lumbar_flexion") ||
      on(lower, "knee_valgus") ||
      on(upper, "bar_drifts_forward") ||
      on(trunk, "lumbar_extension_sway_back");
    if (major) return 1;
    if (on(feet, "heels_lift")) return 2;
    if (asInt(trunk.upright_torso, 1) === 0) return 2;
    return 3;
  }

  if (testName === "hurdle_step") {
    const pelvis = data.pelvis_core_control || {};
    const stepping = data.stepping_leg || {};
    const stance = data.stance_leg || {};
    if (on(stepping, "toe_drag") || on(pelvis, "loss_of_balance")) return 1;
    if (on(pelvis, "excessive_rotation") || on(stance, "knee_valgus") || on(stance, "knee_varus")) return 2;
    return 3;
  }

  if (testName === "inline_lunge") {
    const alignment = data.alignment || {};
    const lower = data.lower_body_control || {};
    const balance = data.balance_stability || {};
    if (on(balance, "loss_of_balance")) return 1;
    if (
      on(alignment, "excessive_forward_lean") ||
      on(alignment, "lateral_shift") ||
      on(lower, "knee_valgus") ||
      on(lower, "heel_lift")
    ) {
      return 2;
    }
    return 3;
  }

  if (testName === "shoulder_mobility") {
    const reach = data.reach_quality || {};
    const compensation = data.compensation || {};
    if (on(reach, "excessive_gap") || on(reach, "asymmetry_present")) return 1;
    if (on(compensation, "rib_flare") || on(compensation, "scapular_winging")) return 2;
    if (on(reach, "hands_within_fist_distance")) return 3;
    return 2;
  }

  if (testName === "active_straight_leg_raise") {
    const nonMoving = data.non_moving_leg || {};
    const moving = data.moving_leg || {};
    const pelvic = data.pelvic_control || {};
    if (on(moving, "lt_60_hip_flexion") || on(nonMoving, "foot_lifts_off_floor")) return 1;
    if (on(pelvic, "anterior_tilt") || on(moving, "hamstring_restriction")) return 2;
    if (on(moving, "gt_80_hip_flexion")) return 3;
    return 2;
  }

  if (testName === "trunk_stability_pushup") {
    const core = data.core_control || {};
    const body = data.body_alignment || {};
    const upper = data.upper_body || {};
    if (on(core, "hips_lag") || on(body, "sagging_hips")) return 1;
    if (on(upper, "uneven_arm_push") || on(upper, "shoulder_instability")) return 2;
    return 3;
  }

  if (testName === "rotary_stability") {
    const diagonal = data.diagonal_pattern || {};
    const spinal = data.spinal_control || {};
    if (on(diagonal, "unable_to_complete")) return 1;
    if (on(diagonal, "loss_of_balance") || on(spinal, "excessive_rotation")) return 2;
    if (on(diagonal, "smooth_controlled")) return 3;
    return 2;
  }

  return 3;
};

const commentSide = (text = "") => {
  const left = LEFT_RE.test(text);
  const right = RIGHT_RE.test(text);
  if (left && !right) return "left";
  if (right && !left) return "right";
  return null;
};

const observationSide = (data = {}) => {
  const blobs = Object.values(data).filter((v) => v && typeof v === "object");
  const left = blobs.some((s) => on(s, "left_side_deficit"));
  const right = blobs.some((s) => on(s, "right_side_deficit"));
  if (left && !right) return "left";
  if (right && !left) return "right";
  return commentSide(data.comment);
};

export const scoreMovement = (testName, data = {}) => {
  if (data.clearing_pain || data.pain === true || on(data.pain, "pain_reported")) {
    return { score: 0, l_score: 0, r_score: 0, source: "pain" };
  }

  let calculated;
  if (hasFaultInputs(data)) {
    calculated = calculateScoreFromFaults(testName, data);
  } else if (hasQualityInputs(data)) {
    calculated = 3;
  } else {
    calculated = 2;
  }

  const side = observationSide(data);
  let l_score = calculated;
  let r_score = calculated;
  if (side === "left") {
    r_score = 3;
  } else if (side === "right") {
    l_score = 3;
  }

  const score = Math.min(l_score, r_score, calculated);
  return { score, l_score, r_score, source: hasFaultInputs(data) ? "faults" : hasQualityInputs(data) ? "quality" : "unscored" };
};

export const stampComputedScores = (payload, movements = []) => {
  const next = { ...payload, use_manual_scores: false };
  for (const movement of movements) {
    const current = payload[movement.id] || {};
    const scored = scoreMovement(movement.id, current);
    const row = { ...current, score: scored.score };
    if (movement.score_config?.type === "asymmetrical") {
      row.l_score = scored.l_score;
      row.r_score = scored.r_score;
    }
    if (typeof row.pain === "boolean") {
      if (row.pain) row.score = 0;
      delete row.pain;
    }
    next[movement.id] = row;
  }
  return next;
};
