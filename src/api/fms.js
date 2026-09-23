import { apiFetch } from "./clients";

export const submitFMSAssessment = async (payload) => {
  return apiFetch("/generate-workout", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const submitAssessmentSession = async (payload) => {
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

export const getAssessmentBatteries = async () => apiFetch("/assessment/batteries");

export const estimateOneRm = async (payload) =>
  apiFetch("/tools/estimate-1rm", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getLoadTables = async () => apiFetch("/tools/load-tables");
