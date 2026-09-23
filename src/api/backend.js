import { apiFetch } from "./clients";

export const getFmsSpec = async () => {
  return apiFetch("/fms/spec");
};

export const getMethodology = async () => {
  return apiFetch("/methodology");
};

export const saveAssessment = async (payload) => {
  const { student_id, ...data } = payload;
  if (!student_id) throw new Error("Student ID required for saving assessment");
  return apiFetch(`/students/${student_id}/assessments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const getAssessments = async (studentId) => {
  return apiFetch(`/students/${studentId}/assessments`);
};

export const saveWorkout = async (payload) => {
  const { student_id, ...data } = payload;
  if (!student_id) throw new Error("Student ID required for saving workout");
  return apiFetch(`/students/${student_id}/workouts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const getStudentWorkouts = async (studentId) => {
  return apiFetch(`/students/${studentId}/workouts`);
};

export const getStudent = async (studentId) => {
  return apiFetch(`/students/${studentId}`);
};

export const getLiftMaxHistory = async (studentId) => {
  return apiFetch(`/students/${studentId}/lift-maxes/history`);
};

export const updateStudent = async (studentId, payload) => {
  return apiFetch(`/students/${studentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const getProgram = async (studentId, programId) => {
  return apiFetch(`/students/${studentId}/workouts/${programId}`);
};

export const reviewProgram = async (studentId, programId, payload) => {
  return apiFetch(`/students/${studentId}/workouts/${programId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const getCoachInsights = async () => apiFetch("/me/insights");

export const getMe = async () => apiFetch("/me");

export const getModules = async () => apiFetch("/modules");

export const unlockAdminSession = async (gateSecret) =>
  apiFetch("/admin/session", {
    method: "POST",
    body: JSON.stringify({ gate_secret: gateSecret }),
  });

export const getAdminOverview = async () => apiFetch("/admin/overview");

export const getAdminCoaches = async () => apiFetch("/admin/coaches");

export const patchAdminCoach = async (coachId, payload) =>
  apiFetch(`/admin/coaches/${coachId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const patchAdminModule = async (moduleId, payload) =>
  apiFetch(`/admin/modules/${moduleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const getBlock = async (studentId, blockId) =>
  apiFetch(`/students/${studentId}/blocks/${blockId}`);

export const getBlockWeek = async (studentId, blockId, weekIndex) =>
  apiFetch(`/students/${studentId}/blocks/${blockId}/weeks/${weekIndex}`);

export const createShare = async (studentId, programId) =>
  apiFetch(`/students/${studentId}/workouts/${programId}/share`, { method: "POST" });

export const revokeShare = async (studentId, programId) =>
  apiFetch(`/students/${studentId}/workouts/${programId}/share/revoke`, { method: "POST" });

export const downloadExport = async (studentId, programId, kind) => {
  const path = `/students/${studentId}/workouts/${programId}/export.${kind}`;
  const res = await apiFetch(path);
  if (res instanceof Response) {
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fitai-week-${programId}.${kind}`;
    a.click();
    URL.revokeObjectURL(url);
  } else {
    window.open(`/api${path}`, "_blank");
  }
};
