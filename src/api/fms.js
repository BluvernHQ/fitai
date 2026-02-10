import { apiFetch } from "./clients";

/**
 * Submits the FMS assessment payload to generate a workout.
 *
 * @param {Object} payload - The structured FMS data (use adaptFMSPayload first).
 * @returns {Promise<Object>} - The generated workout plan.
 */
export const submitFMSAssessment = async (payload) => {
  return apiFetch("/generate-workout", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

/**
 * Generates a workout based on manually edited calculated scores.
 *
 * @param {Object} payload - { calculated_scores: { ... } }
 * @returns {Promise<Object>} - The generated workout plan.
 */
export const generateWorkoutFromScores = async (payload) => {
  return apiFetch("/generate-workout-from-scores", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
