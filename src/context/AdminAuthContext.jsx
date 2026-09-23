import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "./authContext";
import {
  clearAdminSession,
  getAdminSession,
  hasAdminSession,
  setAdminSession,
} from "../lib/adminSession";
import { unlockAdminSession } from "../api/backend";

const AdminAuthContext = createContext(null);

export function AdminAuthProvider({ children }) {
  const { user, logout: logoutFirebase } = useAuth();
  const [session, setSession] = useState(() => getAdminSession());

  useEffect(() => {
    setSession(getAdminSession());
  }, [user]);

  const unlock = useCallback(async ({ email, password, gateSecret, loginFn }) => {
    await loginFn(email, password);
    const payload = await unlockAdminSession(gateSecret);
    setAdminSession({
      token: payload.admin_token,
      expires_at: payload.expires_at,
      coach: payload.coach,
    });
    const next = getAdminSession();
    setSession(next);
    return next;
  }, []);

  const lock = useCallback(() => {
    clearAdminSession();
    setSession(null);
  }, []);

  const exitAdmin = useCallback(async ({ signOutFirebase = false } = {}) => {
    clearAdminSession();
    setSession(null);
    if (signOutFirebase) {
      await logoutFirebase();
    }
  }, [logoutFirebase]);

  const value = useMemo(
    () => ({
      unlocked: Boolean(session?.token) && hasAdminSession(),
      session,
      unlock,
      lock,
      exitAdmin,
    }),
    [session, unlock, lock, exitAdmin],
  );

  return <AdminAuthContext.Provider value={value}>{children}</AdminAuthContext.Provider>;
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) throw new Error("useAdminAuth must be used within AdminAuthProvider");
  return ctx;
}
