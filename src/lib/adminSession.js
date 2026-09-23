const STORAGE_KEY = "fitai_admin_session";

export function getAdminSession() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data?.token || !data?.expires_at) return null;
    if (Number(data.expires_at) * 1000 <= Date.now()) {
      clearAdminSession();
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

export function getAdminSessionToken() {
  return getAdminSession()?.token || null;
}

export function setAdminSession({ token, expires_at, coach }) {
  sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      token,
      expires_at,
      coach: coach || null,
      unlocked_at: Date.now(),
    }),
  );
}

export function clearAdminSession() {
  sessionStorage.removeItem(STORAGE_KEY);
}

export function hasAdminSession() {
  return Boolean(getAdminSessionToken());
}
