import fmsData from "../data/fms-v1.json";

/**
 * Adapts the flat FMS assessment input into the structured backend format.
 * Groups observations by section and prepares for scoring logic.
 *
 * @param {Object} specPayload - The payload containing { assessment_input, spec_version }
 * @returns {Object} Structured payload matching backend expectations
 */
export const adaptFMSPayload = (specPayload) => {
  const scores = specPayload.assessment_input || {};
  const adapted = {
    use_manual_scores: false, // Default logic, can be exposed to UI later if needed
  };

  // Iterate over movements defined in the spec to ensure structure matching Pydantic
  fmsData.movements.forEach((movement) => {
    const inputScores = scores[movement.id] || {};

    // 1. Top Level Scores
    // 1. Top Level Scores
    // Since use_manual_scores is false, we explicitly send 0 for scores to let the backend calculate them.
    // This prevents potential inconsistencies (e.g. sending score: 3 when pain is present) that cause backend 500 errors.
    const movementData = {
      score: 0,
    };

    if (movement.score_config?.type === "asymmetrical") {
      movementData.l_score = 0;
      movementData.r_score = 0;
    }

    if (movement.score_config?.clearing_test) {
      movementData.clearing_pain = Boolean(inputScores.clearing_pain);
    }

    // 2. Sections (Nested Pydantic Models)
    movement.sections.forEach((section) => {
      const sectionData = {};

      section.observations.forEach((obs) => {
        // Validation: Ensure we strictly pass integers
        const rawVal = inputScores[obs.key];
        sectionData[obs.key] = parseInt(rawVal || 0, 10);
      });

      // Assign section data to movement using the exact ID from spec
      movementData[section.id] = sectionData;
    });

    adapted[movement.id] = movementData;
  });

  return adapted;
};
