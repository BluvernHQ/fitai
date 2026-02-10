import { apiFetch } from "./clients";

/**
 * Save a new assessment.
 * POST /students/:id/assessments
 */
export const saveAssessment = async (payload) => {
  const { student_id, ...data } = payload;
  if (!student_id) throw new Error("Student ID required for saving assessment");

  return apiFetch(`/students/${student_id}/assessments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
};

/**
 * Get assessments for a student.
 * GET /students/:id/assessments
 */
export const getAssessments = async (studentId) => {
  return apiFetch(`/students/${studentId}/assessments`);
};

/**
 * Save a generated workout.
 * POST /students/:id/workouts
 */
export const saveWorkout = async (payload) => {
  const { student_id, ...data } = payload;
  if (!student_id) throw new Error("Student ID required for saving workout");

  return apiFetch(`/students/${student_id}/workouts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
};

/**
 * Get all workouts for a student.
 * GET /students/:id/workouts
 */
export const getStudentWorkouts = async (studentId) => {
  return apiFetch(`/students/${studentId}/workouts`);
};

/**
 * Get student details.
 * GET /students/:id
 */
export const getStudent = async (studentId) => {
  return apiFetch(`/students/${studentId}`);
};
