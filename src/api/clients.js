import { getIdToken } from "../firebase/auth";

const API_BASE = "/api";

export const publicFetch = async (path, options = {}) => {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "API error");
  }
  return response.json();
};

async function readError(response) {
  const text = await response.text();
  try {
    const body = JSON.parse(text);
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((item) => item.msg || item).join("; ");
    }
  } catch {
    /* use raw text */
  }
  return text || `API error ${response.status}`;
}

export const apiFetch = async (path, options = {}) => {
  const token = await getIdToken();
  if (!token) {
    throw new Error("Sign in required");
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  if ((response.headers.get("content-type") || "").includes("application/json")) {
    return response.json();
  }
  return response;
};
