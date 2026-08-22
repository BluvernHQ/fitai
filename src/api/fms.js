import { apiFetch } from "./clients";

export const submitFMSAssessment = async (payload) => {
  return apiFetch("/generate-workout", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const generateWorkoutFromScores = async (payload) => {
  return apiFetch("/generate-workout-from-scores", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
