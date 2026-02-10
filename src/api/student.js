import { apiFetch } from "./clients";

export const fetchStudents = () => {
  return apiFetch("/students");
};

export const createStudent = (student) => {
  return apiFetch("/students", {
    method: "POST",
    body: JSON.stringify(student),
  });
};
