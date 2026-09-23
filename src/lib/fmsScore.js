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

const META_KEYS = new Set([
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
]);

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

const emptySectionMap = (sections = []) => {
  const out = {};
  for (const section of sections) {
    out[section.id] = {};
    for (const obs of section.observations || []) {
      out[section.id][obs.key] = 0;
    }
  }
  return out;
};

/** Build / migrate movement row so asymmetrical screens always have left + right nests. */
export const ensureSideStructure = (movement, data = {}) => {
  const row = { ...data };
  if (movement?.score_config?.type !== "asymmetrical") {
    if (!row.sections_initialized) {
      for (const section of movement?.sections || []) {
        if (!row[section.id]) {
          row[section.id] = {};
          for (const obs of section.observations || []) row[section.id][obs.key] = 0;
        }
      }
    }
    return row;
  }

  const hasNested = row.left && typeof row.left === "object" && row.right && typeof row.right === "object";
  if (!hasNested) {
    const flat = {};
    for (const section of movement.sections || []) {
      if (row[section.id] && typeof row[section.id] === "object") {
        flat[section.id] = { ...row[section.id] };
      }
    }
    const left = Object.keys(flat).length ? flat : emptySectionMap(movement.sections);
    const right = emptySectionMap(movement.sections);
    row.left = left;
    row.right = right;
    for (const section of movement.sections || []) {
      delete row[section.id];
    }
  } else {
    for (const section of movement.sections || []) {
      if (!row.left[section.id]) {
        row.left[section.id] = {};
        for (const obs of section.observations || []) row.left[section.id][obs.key] = 0;
      }
      if (!row.right[section.id]) {
        row.right[section.id] = {};
        for (const obs of section.observations || []) row.right[section.id][obs.key] = 0;
      }
    }
  }
  if (row.l_score == null) row.l_score = 2;
  if (row.r_score == null) row.r_score = 2;
  return row;
};

const walkObservationSections = (data = {}, visitor) => {
  for (const [key, value] of Object.entries(data)) {
    if (META_KEYS.has(key)) continue;
    if (!value || typeof value !== "object") continue;
    // nested left/right
    if (key === "left" || key === "right") continue;
    for (const [name, severity] of Object.entries(value)) {
      if (typeof severity === "object") continue;
      visitor(name, severity, key);
    }
  }
};

const hasFaultInputs = (data = {}) => {
  if (data.clearing_pain || data.pain === true) return true;
  if (data.pain && typeof data.pain === "object" && on(data.pain, "pain_reported")) return true;
  let found = false;
  walkObservationSections(data, (name, severity) => {
    if (asInt(severity) > 0 && isFaultKey(name)) found = true;
  });
  return found;
};

const hasQualityInputs = (data = {}) => {
  let found = false;
  walkObservationSections(data, (name, severity) => {
    if (asInt(severity) > 0 && isQualityKey(name)) found = true;
  });
  return found;
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

const scoreSideBundle = (testName, sideData = {}, shared = {}) => {
  const bundle = {
    ...sideData,
    clearing_pain: shared.clearing_pain,
    pain: shared.pain,
  };
  if (shared.clearing_pain || shared.pain === true || on(shared.pain || {}, "pain_reported")) {
    return { score: 0, source: "pain" };
  }
  if (hasFaultInputs(bundle)) {
    return { score: calculateScoreFromFaults(testName, bundle), source: "faults" };
  }
  if (hasQualityInputs(bundle)) {
    return { score: 3, source: "quality" };
  }
  // Do not invent a 2 — coach must mark faults or quality
  return { score: null, source: "unscored" };
};

export const scoreMovement = (testName, data = {}) => {
  if (data.clearing_pain || data.pain === true || on(data.pain || {}, "pain_reported")) {
    return { score: 0, l_score: 0, r_score: 0, source: "pain", complete: true };
  }

  const hasSides =
    data.left &&
    typeof data.left === "object" &&
    data.right &&
    typeof data.right === "object";

  if (hasSides) {
    const shared = { clearing_pain: data.clearing_pain, pain: data.pain };
    const left = scoreSideBundle(testName, data.left, shared);
    const right = scoreSideBundle(testName, data.right, shared);
    const bothScored = left.score != null && right.score != null;
    const score = bothScored ? Math.min(left.score, right.score) : null;
    const source =
      left.source === "pain" || right.source === "pain"
        ? "pain"
        : left.source === "faults" || right.source === "faults"
          ? "faults"
          : left.source === "quality" || right.source === "quality"
            ? "quality"
            : "unscored";
    return {
      score,
      l_score: left.score,
      r_score: right.score,
      source: bothScored ? source : "unscored",
      complete: bothScored,
      leftComplete: left.score != null,
      rightComplete: right.score != null,
    };
  }

  // Symmetrical / flat: no default 2
  let calculated = null;
  let source = "unscored";
  if (hasFaultInputs(data)) {
    calculated = calculateScoreFromFaults(testName, data);
    source = "faults";
  } else if (hasQualityInputs(data)) {
    calculated = 3;
    source = "quality";
  }
  return {
    score: calculated,
    l_score: calculated,
    r_score: calculated,
    source,
    complete: calculated != null,
    leftComplete: calculated != null,
    rightComplete: calculated != null,
  };
};

export const formatScore = (score) => (score == null ? "—" : String(score));

export const stampComputedScores = (payload, movements = []) => {
  const next = { ...payload, use_manual_scores: false };
  for (const movement of movements) {
    const current = ensureSideStructure(movement, payload[movement.id] || {});
    const scored = scoreMovement(movement.id, current);
    const row = { ...current, score: scored.score };
    if (movement.score_config?.type === "asymmetrical") {
      row.l_score = scored.l_score;
      row.r_score = scored.r_score;
    }
    if (typeof row.pain === "boolean") {
      if (row.pain) {
        row.score = 0;
        if ("l_score" in row) row.l_score = 0;
        if ("r_score" in row) row.r_score = 0;
      }
      delete row.pain;
    }
    next[movement.id] = row;
  }
  return next;
};

/** True when every movement has observations (both sides for asymmetrical). */
export const fmsSessionComplete = (payload, movements = []) =>
  movements.every((m) => scoreMovement(m.id, ensureSideStructure(m, payload[m.id] || {})).complete);

