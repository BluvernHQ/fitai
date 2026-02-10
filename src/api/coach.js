import { apiFetch } from "./clients";

export const fetchMe = () => {
  return apiFetch("/me");
};

export const registerCoach = (coachData) => {
  return apiFetch("/coaches", {
    method: "POST",
    body: JSON.stringify(coachData),
  });
};
