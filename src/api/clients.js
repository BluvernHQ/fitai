import { getIdToken } from "../firebase/auth";

const API_BASE = "/api";

export const apiFetch = async (path, options = {}) => {
  const token = await getIdToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Auth failed → force logout later (we’ll wire this properly soon)
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "API error");
  }

  return response.json();
};
